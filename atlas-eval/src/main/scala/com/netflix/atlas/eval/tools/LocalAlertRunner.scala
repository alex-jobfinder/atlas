package com.netflix.atlas.eval.tools

import com.netflix.atlas.core.db.{Database, StaticDatabase}
import com.netflix.atlas.core.model.{DataExpr, TimeSeries}
import com.netflix.atlas.eval.graph.Grapher
import com.typesafe.config.{Config, ConfigFactory, ConfigValueFactory}
import org.apache.pekko.http.scaladsl.model.Uri

import java.io.{FileOutputStream, PrintWriter}
import java.time.Instant
import java.util.zip.GZIPOutputStream
import com.netflix.atlas.chart.JsonCodec

/**
  * Alert evaluation tool that extends LocalGraphRunner for alerting scenarios.
  * Evaluates alert expressions against synthetic time series data and generates
  * alert reports, notifications, and visualizations.
  *
  * Examples:
  *   sbt 'project atlas-eval' \
  *     'runMain com.netflix.atlas.eval.tools.LocalAlertRunner \
  *        --preset sps \
  *        --alert "name,sps,:eq,(,nf.cluster,),:by,50e3,:gt" \
  *        --threshold 50000 \
  *        --s e-1w --e 2012-01-01T00:00 --tz UTC \
  *        --out target/manual/alert_report.json'
  */
object LocalAlertRunner {

  private case class AlertResult(
    timestamp: Instant,
    expression: String,
    threshold: Double,
    triggered: Boolean,
    value: Double,
    tags: Map[String, String],
    severity: String = "WARNING"
  )

  private case class Args(
    preset: String = "sps",
    alert: String = "",           // Alert expression (replaces 'q' for alerts)
    threshold: Option[Double] = None,  // Threshold value for comparison
    operator: String = "gt",      // Comparison operator: gt, lt, ge, le
    severity: String = "WARNING", // Alert severity: CRITICAL, WARNING, INFO
    s: Option[String] = None,
    e: Option[String] = None,
    tz: Option[String] = None,
    step: Option[String] = None,
    noLegend: Boolean = false,
    theme: Option[String] = None,
    layout: Option[String] = None,
    w: Option[Int] = None,
    h: Option[Int] = None,
    palette: Option[String] = None,
    style: Option[String] = None,
    out: String = "",
    emitV2: Option[String] = None,
    saveTemplate: Option[String] = None,
    alertOutput: Option[String] = None,  // Alert-specific output format
    generateChart: Boolean = true,      // Whether to generate chart visualization
    generateReport: Boolean = true,     // Whether to generate alert report
    showVisualAlert: Boolean = true     // Whether to show visual alert threshold on chart
  )

  def main(argv: Array[String]): Unit = {
    val args = parseArgs(argv.toList)
    if (args.isEmpty) {
      printUsage()
      sys.exit(2)
    }
    val a = args.get

    val db = loadPresetDb(a.preset)
    val grapher = Grapher(ConfigFactory.load())
    
    // Build alert expression with threshold
    val alertExpr = buildAlertExpression(a)
    val uri = buildUri(a, alertExpr)

    // Evaluate the alert expression
    val alertResults = evaluateAlert(grapher, uri, db, a)
    
    // Generate outputs
    if (a.generateChart) {
      generateChart(grapher, db, a)
    }
    
    if (a.generateReport) {
      generateAlertReport(alertResults, a)
    }
    
    // Optionally emit V2 GraphDef JSON
    a.emitV2.foreach { path =>
      val res = grapher.evalAndRender(uri, db)
      val gdef = buildGraphDefFromDb(grapher, res.config, db)
      writeV2(path, gdef)
      println(s"Wrote V2: ${new java.io.File(path).getAbsolutePath}")
    }

    // Optionally save a reusable args template
    a.saveTemplate.foreach { path =>
      writeTemplate(path, a)
      println(s"Saved template: ${new java.io.File(path).getAbsolutePath}")
    }
  }

  private def buildAlertExpression(a: Args): String = {
    val threshold = a.threshold.getOrElse(0.0)
    val operator = a.operator.toLowerCase match {
      case "gt" => ":gt"
      case "lt" => ":lt" 
      case "ge" => ":ge"
      case "le" => ":le"
      case _ => ":gt"
    }
    
    s"${a.alert},$threshold,$operator"
  }

  private def buildVisualAlertExpression(a: Args): String = {
    val threshold = a.threshold.getOrElse(0.0)
    val operator = a.operator.toLowerCase
    
    // Create a visual expression that shows both the data and the alert threshold
    val baseExpr = a.alert
    
    // Add threshold line and alert zones based on operator
    operator match {
      case "gt" => 
        s"$baseExpr,:dup,$threshold,:const,:line,2,:lw,red,:color,Alert Threshold,:legend"
      case "lt" => 
        s"$baseExpr,:dup,$threshold,:const,:line,2,:lw,red,:color,Alert Threshold,:legend"
      case "ge" => 
        s"$baseExpr,:dup,$threshold,:const,:line,2,:lw,red,:color,Alert Threshold,:legend"
      case "le" => 
        s"$baseExpr,:dup,$threshold,:const,:line,2,:lw,red,:color,Alert Threshold,:legend"
      case _ => 
        s"$baseExpr,:dup,$threshold,:const,:line,2,:lw,red,:color,Alert Threshold,:legend"
    }
  }

  private def evaluateAlert(
    grapher: Grapher, 
    uri: Uri, 
    db: Database, 
    args: Args
  ): List[AlertResult] = {
    val res = grapher.evalAndRender(uri, db)
    val threshold = args.threshold.getOrElse(0.0)
    val operator = args.operator.toLowerCase
    
    // Extract time series data and evaluate alert conditions
    val dataExprs = res.config.exprs.flatMap(_.expr.dataExprs).distinct
    val result: Map[DataExpr, List[TimeSeries]] = dataExprs.map { expr =>
      expr -> db.execute(res.config.evalContext, expr)
    }.toMap
    
    val evalResults = res.config.exprs.flatMap { exprConfig =>
      val context = res.config.evalContext
      val tsList = exprConfig.expr.eval(context, result).data
      
      tsList.map { ts =>
        val boundedData = ts.data.bounded(res.config.evalContext.start, res.config.evalContext.end)
        val latestValue = if (boundedData.data.nonEmpty) boundedData.data.last else Double.NaN
        val triggered = operator match {
          case "gt" => latestValue > threshold
          case "lt" => latestValue < threshold
          case "ge" => latestValue >= threshold
          case "le" => latestValue <= threshold
          case _ => latestValue > threshold
        }
        
        AlertResult(
          timestamp = Instant.now(),
          expression = args.alert,
          threshold = threshold,
          triggered = triggered,
          value = latestValue,
          tags = ts.tags,
          severity = args.severity
        )
      }
    }
    
    evalResults.toList
  }

  private def generateChart(
    grapher: Grapher, 
    db: Database, 
    args: Args
  ): Unit = {
    // Choose expression based on whether to show visual alert
    val chartExpr = if (args.showVisualAlert) {
      buildVisualAlertExpression(args)
    } else {
      buildAlertExpression(args)
    }
    val chartUri = buildUri(args, chartExpr)
    
    val res = grapher.evalAndRender(chartUri, db)
    val out = new java.io.File(args.out)
    Option(out.getParentFile).foreach(_.mkdirs())
    val fos = new FileOutputStream(out)
    try fos.write(res.data) finally fos.close()
    println(s"Wrote chart: ${out.getAbsolutePath}")
  }

  private def generateAlertReport(results: List[AlertResult], args: Args): Unit = {
    val alertOutput = args.alertOutput.getOrElse(args.out.replaceAll("\\.(png|jpg|jpeg)$", ".json"))
    val reportFile = new java.io.File(alertOutput)
    Option(reportFile.getParentFile).foreach(_.mkdirs())
    
    val writer = new PrintWriter(reportFile)
    try {
      writer.println("{")
      writer.println(s"""  "timestamp": "${Instant.now().toString}",""")
      writer.println(s"""  "alert_expression": "${args.alert}",""")
      writer.println(s"""  "threshold": ${args.threshold.getOrElse(0.0)},""")
      writer.println(s"""  "operator": "${args.operator}",""")
      writer.println(s"""  "severity": "${args.severity}",""")
      writer.println(s"""  "total_series": ${results.length},""")
      writer.println(s"""  "triggered_count": ${results.count(_.triggered)},""")
      writer.println("  \"results\": [")
      
      results.zipWithIndex.foreach { case (result, index) =>
        writer.println("    {")
        writer.println(s"""      "timestamp": "${result.timestamp}",""")
        writer.println(s"""      "triggered": ${result.triggered},""")
        writer.println(s"""      "value": ${result.value},""")
        writer.println(s"""      "threshold": ${result.threshold},""")
        writer.println(s"""      "severity": "${result.severity}",""")
        writer.println(s"""      "tags": ${formatTags(result.tags)}""")
        writer.println("    }" + (if (index < results.length - 1) "," else ""))
      }
      
      writer.println("  ]")
      writer.println("}")
    } finally {
      writer.close()
    }
    
    println(s"Wrote alert report: ${reportFile.getAbsolutePath}")
    
    // Print summary to console
    val triggered = results.filter(_.triggered)
    println(s"\n=== ALERT SUMMARY ===")
    println(s"Total time series evaluated: ${results.length}")
    println(s"Alerts triggered: ${triggered.length}")
    println(s"Severity: ${args.severity}")
    
    if (triggered.nonEmpty) {
      println(s"\n=== TRIGGERED ALERTS ===")
      triggered.foreach { alert =>
        println(s"  ${alert.tags.getOrElse("name", "unknown")}: ${alert.value} ${args.operator} ${alert.threshold}")
      }
    }
  }

  private def formatTags(tags: Map[String, String]): String = {
    val tagPairs = tags.map { case (k, v) => s""""$k": "$v"""" }
    s"{${tagPairs.mkString(", ")}}"
  }

  private def buildUri(a: Args, alertExpr: String): Uri = {
    import scala.collection.mutable
    val params = mutable.ListBuffer[(String, String)]()

    val q = a.style match {
      case Some(st) if st.nonEmpty => s"$alertExpr,:${st.toLowerCase}"
      case _                       => alertExpr
    }
    params += ("q" -> q)
    a.s.foreach(v => params += ("s" -> v))
    a.e.foreach(v => params += ("e" -> v))
    a.tz.foreach(v => params += ("tz" -> v))
    a.step.foreach(v => params += ("step" -> v))
    if (a.noLegend) params += ("no_legend" -> "1")
    a.theme.foreach(v => params += ("theme" -> v))
    a.layout.foreach(v => params += ("layout" -> v))
    a.w.foreach(v => params += ("w" -> v.toString))
    a.h.foreach(v => params += ("h" -> v.toString))
    a.palette.foreach(v => params += ("palette" -> v))

    val query = Uri.Query(params.toSeq: _*)
    Uri("http://local/api/v1/graph").withQuery(query)
  }

  // Map friendly preset names to DataSet names (see atlas-core/.../DataSet.scala)
  private def loadPresetDb(name: String): Database = name.toLowerCase match {
    case "sps" | "small" => new StaticDatabase(dbConfigWithDataset("small"))
    case "alerts" | "alert" => new StaticDatabase(dbConfigWithDataset("alert"))
    case "demo" => StaticDatabase.demo
    case "range" => StaticDatabase.range(1, 5)
    case other =>
      System.err.println(s"Unknown preset '$other', defaulting to 'small'")
      new StaticDatabase(dbConfigWithDataset("small"))
  }

  private def dbConfigWithDataset(ds: String): Config = {
    val root = ConfigFactory.load()
    val base = root.getConfig("atlas.core.db")
    base.withValue("dataset", ConfigValueFactory.fromAnyRef(ds))
  }

  private def parseArgs(args: List[String]): Option[Args] = {
    @annotation.tailrec
    def loop(rest: List[String], a: Args): Option[Args] = rest match {
      case Nil => if (a.alert.nonEmpty && a.out.nonEmpty) Some(a) else None
      case "--preset" :: v :: t => loop(t, a.copy(preset = v))
      case "--alert" :: v :: t => loop(t, a.copy(alert = v))
      case "--threshold" :: v :: t => loop(t, a.copy(threshold = Some(v.toDouble)))
      case "--operator" :: v :: t => loop(t, a.copy(operator = v))
      case "--severity" :: v :: t => loop(t, a.copy(severity = v))
      case "--s" :: v :: t => loop(t, a.copy(s = Some(v)))
      case "--e" :: v :: t => loop(t, a.copy(e = Some(v)))
      case "--tz" :: v :: t => loop(t, a.copy(tz = Some(v)))
      case "--step" :: v :: t => loop(t, a.copy(step = Some(v)))
      case "--no-legend" :: t => loop(t, a.copy(noLegend = true))
      case "--theme" :: v :: t => loop(t, a.copy(theme = Some(v)))
      case "--layout" :: v :: t => loop(t, a.copy(layout = Some(v)))
      case "--w" :: v :: t => loop(t, a.copy(w = Some(v.toInt)))
      case "--h" :: v :: t => loop(t, a.copy(h = Some(v.toInt)))
      case "--palette" :: v :: t => loop(t, a.copy(palette = Some(v)))
      case "--style" :: v :: t => loop(t, a.copy(style = Some(v)))
      case "--emit-v2" :: v :: t => loop(t, a.copy(emitV2 = Some(v)))
      case "--save-template" :: v :: t => loop(t, a.copy(saveTemplate = Some(v)))
      case "--alert-output" :: v :: t => loop(t, a.copy(alertOutput = Some(v)))
      case "--no-chart" :: t => loop(t, a.copy(generateChart = false))
      case "--no-report" :: t => loop(t, a.copy(generateReport = false))
      case "--no-visual-alert" :: t => loop(t, a.copy(showVisualAlert = false))
      case ("--out" | "-o") :: v :: t => loop(t, a.copy(out = v))
      case _ => None
    }
    loop(args, Args())
  }

  private def printUsage(): Unit = {
    val msg =
      s"""
         |Usage:
         |  runMain com.netflix.atlas.eval.tools.LocalAlertRunner --preset sps \\
         |    --alert "name,sps,:eq,(,nf.cluster,),:by" \\
         |    --threshold 50000 --operator gt --severity CRITICAL \\
         |    --s e-1w --e 2012-01-01T00:00 --tz UTC \\
         |    --w 700 --h 300 --theme light \\
         |    --out target/manual/alert_chart.png \\
         |    --alert-output target/manual/alert_report.json
         |
         |Alert-specific options:
         |  --alert <expr>           Alert expression (replaces --q)
         |  --threshold <value>      Threshold value for comparison
         |  --operator <op>          Comparison operator: gt, lt, ge, le (default: gt)
         |  --severity <level>       Alert severity: CRITICAL, WARNING, INFO (default: WARNING)
         |  --alert-output <file>    Alert report output file (default: auto-generated)
         |  --no-chart               Skip chart generation
         |  --no-report              Skip alert report generation
         |  --no-visual-alert        Skip visual alert threshold on chart
         |
         |Optional:
         |  --emit-v2 target/manual/alert.v2.json.gz   # write GraphDef (V2) alongside PNG
         |  --save-template scripts/alert.args         # save a reusable args file
         |
         |Notes:
         |  - Alert expressions use Atlas Query Language (AQL)
         |  - Threshold comparisons are applied to the latest value in each time series
         |  - Alert reports include JSON output with triggered alerts and metadata
         |  - Charts show the alert expression visualization with threshold lines
         |""".stripMargin
    System.err.println(msg)
  }

  /** Build a GraphDef for V2 emission using the same data as the rendered PNG. */
  private def buildGraphDefFromDb(
    grapher: Grapher,
    config: com.netflix.atlas.eval.graph.GraphConfig,
    db: Database
  ) = {
    val dataExprs = config.exprs.flatMap(_.expr.dataExprs).distinct
    val result: Map[DataExpr, List[TimeSeries]] = dataExprs.map { expr =>
      expr -> db.execute(config.evalContext, expr)
    }.toMap
    grapher.create(config, _.expr.eval(config.evalContext, result))
  }

  /** Write GraphDef in V2 JSON (gzipped if path ends with .gz). */
  private def writeV2(path: String, gdef: com.netflix.atlas.chart.model.GraphDef): Unit = {
    val f = new java.io.File(path)
    Option(f.getParentFile).foreach(_.mkdirs())
    val raw: java.io.OutputStream = new FileOutputStream(f)
    val out = if (path.toLowerCase.endsWith(".gz")) new GZIPOutputStream(raw) else raw
    try JsonCodec.encode(out, gdef) finally out.close()
  }

  /** Save a simple args template that can be reused with runMain. */
  private def writeTemplate(path: String, a: Args): Unit = {
    val parts = Seq(
      Some(s"--preset ${a.preset}"),
      Some(s"--alert \"${a.alert}\""),
      a.threshold.map(v => s"--threshold $v"),
      Some(s"--operator ${a.operator}"),
      Some(s"--severity ${a.severity}"),
      a.style.filter(_.nonEmpty).map(v => s"--style $v").orElse(Some("--style line")),
      a.s.map(v => s"--s $v"),
      a.e.map(v => s"--e $v"),
      a.tz.map(v => s"--tz $v"),
      a.step.map(v => s"--step $v"),
      if (a.noLegend) Some("--no-legend") else None,
      a.theme.map(v => s"--theme $v"),
      a.layout.map(v => s"--layout $v"),
      a.w.map(v => s"--w $v"),
      a.h.map(v => s"--h $v"),
      a.palette.map(v => s"--palette $v"),
      a.emitV2.map(v => s"--emit-v2 $v"),
      a.alertOutput.map(v => s"--alert-output $v"),
      Some(s"--out ${a.out}")
    ).flatten.mkString(" ")
    val file = new java.io.File(path)
    Option(file.getParentFile).foreach(_.mkdirs())
    val content = s"# LocalAlertRunner args template\n$parts\n"
    val fos = new FileOutputStream(file)
    try fos.write(content.getBytes("UTF-8")) finally fos.close()
  }
}
