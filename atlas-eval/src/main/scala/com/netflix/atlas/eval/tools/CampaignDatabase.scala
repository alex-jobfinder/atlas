package com.netflix.atlas.eval.tools

import com.netflix.atlas.core.db.Database
import com.netflix.atlas.core.model.{EvalContext, TimeSeries}
import com.netflix.atlas.core.model.DataExpr
import com.netflix.atlas.core.model.ArrayTimeSeq
import com.netflix.atlas.core.model.DsType
import com.netflix.atlas.core.index.{TagIndex, RoaringTagIndex}
import com.netflix.atlas.core.index.IndexStats

import java.sql.{Connection, DriverManager, ResultSet}
import scala.collection.mutable.ArrayBuffer

/**
 * Custom database adapter for campaign performance data from SQLite.
 * Converts SQL query results to Atlas TimeSeries format.
 */
class CampaignDatabase(dbPath: String, debugLevel: Int = 1) extends Database {

  // Initialize SQLite driver
  Class.forName("org.sqlite.JDBC")

  // Debug helper method
  private def debug(level: Int, message: => String): Unit = {
    if (debugLevel >= level) {
      println(s"[DEBUG-$level] $message")
    }
  }

  // Create index from all available time series data
  val index: TagIndex[TimeSeries] = {
    val allTimeSeries = loadAllTimeSeries()
    new RoaringTagIndex(allTimeSeries.toArray, new IndexStats())
  }

  private def getConnection(): Connection = {
    DriverManager.getConnection(s"jdbc:sqlite:$dbPath")
  }

  private def loadAllTimeSeries(): List[TimeSeries] = {
    // Load all campaign performance data and convert to TimeSeries
    val connection = getConnection()
    try {
      val statement = connection.createStatement()
      val resultSet = statement.executeQuery("""
        SELECT DISTINCT campaign_id FROM campaign_performance
        WHERE campaign_id IS NOT NULL
      """)

      val campaignIds = ArrayBuffer[Int]()
      while (resultSet.next()) {
        campaignIds += resultSet.getInt("campaign_id")
      }

      resultSet.close()
      statement.close()

      // Create TimeSeries for each campaign and metric
      val metrics = List("impressions", "clicks", "video_start")
      val allTimeSeries = ArrayBuffer[TimeSeries]()

      // Use a fixed time range that's properly aligned with step boundaries
      // This is just for the index - actual data will be loaded in execute()
      val baseTime = 1325376000000L // 2012-01-01T00:00:00Z in milliseconds
      val stepSize = 3600000L // 1 hour in milliseconds

      for (campaignId <- campaignIds) {
        for (metric <- metrics) {
          val tags = Map(
            "name" -> metric,
            "campaign_id" -> campaignId.toString
          )

          // Create a simple time series with dummy data for the index
          // The actual data will be loaded in the execute method
          val dummyData = new ArrayTimeSeq(DsType.Gauge, baseTime, stepSize, Array.empty[Double])
          val timeSeries = TimeSeries(tags, s"$metric,campaign_id=$campaignId", dummyData)
          allTimeSeries += timeSeries
        }
      }

      allTimeSeries.toList
    } finally {
      connection.close()
    }
  }

  override def execute(ctxt: EvalContext, expr: DataExpr): List[TimeSeries] = {
    // Extract the metric name and campaign_id from the expression
    val metricName = extractMetricName(expr)
    val campaignId = extractCampaignId(expr)

    // Debug: Print what we're looking for
    debug(1, s"Looking for metric='$metricName', campaign_id=$campaignId")
    debug(1, s"Time range: ${ctxt.start} to ${ctxt.end}")

    // Execute SQL query to get campaign performance data
    val sqlQuery = s"""
      SELECT hour_ts, hour_unix_epoch, impressions, clicks, video_start
      FROM campaign_performance
      WHERE campaign_id = $campaignId
      AND hour_unix_epoch >= ${ctxt.start / 1000}
      AND hour_unix_epoch <= ${ctxt.end / 1000}
      ORDER BY hour_unix_epoch ASC
    """

    debug(2, s"SQL Query: $sqlQuery")

    val connection = getConnection()
    try {
      val statement = connection.createStatement()
      val resultSet = statement.executeQuery(sqlQuery)

      val timeSeriesData = convertResultSetToTimeSeries(resultSet, metricName, campaignId, ctxt)

      debug(1, s"Found ${timeSeriesData.length} time series")

      resultSet.close()
      statement.close()

      timeSeriesData
    } finally {
      connection.close()
    }
  }

  private def convertResultSetToTimeSeries(
    resultSet: ResultSet,
    metricName: String,
    campaignId: Int,
    ctxt: EvalContext
  ): List[TimeSeries] = {

    val timestamps = ArrayBuffer[Long]()
    val values = ArrayBuffer[Double]()

    var rowCount = 0
    while (resultSet.next()) {
      val hourUnixEpoch = resultSet.getLong("hour_unix_epoch")
      val timestampMs = hourUnixEpoch * 1000 // Convert to milliseconds

      val value = metricName match {
        case "impressions" => resultSet.getInt("impressions").toDouble
        case "clicks" => resultSet.getInt("clicks").toDouble
        case "video_start" => resultSet.getInt("video_start").toDouble
        case _ => resultSet.getInt("impressions").toDouble // Default to impressions
      }

      timestamps += timestampMs
      values += value
      rowCount += 1

      debug(3, s"Row $rowCount: timestamp=$timestampMs, value=$value")
    }

    debug(2, s"Processed $rowCount rows from database")

    if (timestamps.isEmpty) {
      debug(1, "No data found in result set")
      return List.empty
    }

    // Create evenly spaced time series with step size
    val stepSize = ctxt.step
    val startTime = ctxt.start
    val endTime = ctxt.end

    // Ensure start time is aligned with step boundary
    val alignedStartTime = (startTime / stepSize) * stepSize

    debug(2, s"Step size: $stepSize, aligned start: $alignedStartTime, end: $endTime")

    val dataArray = createEvenlySpacedData(timestamps.toArray, values.toArray, alignedStartTime, endTime, stepSize)

    debug(2, s"Created data array with ${dataArray.length} points")

    // Create tags for Atlas
    val tags = Map(
      "name" -> metricName,
      "campaign_id" -> campaignId.toString
    )

    // Create TimeSeq and TimeSeries with aligned start time
    val timeSeq = new ArrayTimeSeq(DsType.Gauge, alignedStartTime, stepSize, dataArray)
    val timeSeries = TimeSeries(tags, s"$metricName,campaign_id=$campaignId", timeSeq)

    debug(1, s"Created TimeSeries: ${timeSeries.label}")

    List(timeSeries)
  }

  private def createEvenlySpacedData(
    timestamps: Array[Long],
    values: Array[Double],
    startTime: Long,
    endTime: Long,
    stepSize: Long
  ): Array[Double] = {

    val numSteps = ((endTime - startTime) / stepSize).toInt + 1
    val dataArray = new Array[Double](numSteps)

    // Initialize with NaN
    for (i <- dataArray.indices) {
      dataArray(i) = Double.NaN
    }

    // Fill in actual values
    for (i <- timestamps.indices) {
      val timestamp = timestamps(i)
      val value = values(i)

      val stepIndex = ((timestamp - startTime) / stepSize).toInt
      if (stepIndex >= 0 && stepIndex < numSteps) {
        dataArray(stepIndex) = value
      }
    }

    dataArray
  }

  private def extractMetricName(expr: DataExpr): String = {
    // Parse the expression to extract metric name
    // Look for patterns like "name,impressions,:eq" in the expression
    val exprStr = expr.toString
    val namePattern = """name,(\w+),:eq""".r
    namePattern.findFirstMatchIn(exprStr) match {
      case Some(m) => m.group(1)
      case None => "impressions" // Default fallback
    }
  }

  private def extractCampaignId(expr: DataExpr): Int = {
    // Parse the expression to extract campaign_id
    // Look for patterns like "(,campaign_id,),:by" in the expression
    val exprStr = expr.toString
    val campaignPattern = """\(,campaign_id,\),:by""".r
    if (campaignPattern.findFirstIn(exprStr).isDefined) {
      // For now, return 1 as default - in a real implementation,
      // you might want to return all campaign IDs and handle them separately
      1
    } else {
      1 // Default fallback
    }
  }
}
