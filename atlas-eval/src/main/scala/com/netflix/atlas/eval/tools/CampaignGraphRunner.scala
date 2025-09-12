package com.netflix.atlas.eval.tools

import com.netflix.atlas.core.db.Database
import com.netflix.atlas.eval.graph.Grapher
import com.typesafe.config.ConfigFactory
import org.apache.pekko.http.scaladsl.model.Uri

import java.io.FileOutputStream
import java.util.zip.GZIPOutputStream
import com.netflix.atlas.chart.JsonCodec

/**
 * Custom Atlas Graph Runner for campaign performance data from SQLite database.
 * Extends LocalGraphRunner to work with real campaign data instead of synthetic data.
 *
 * Usage:
 *   sbt 'project atlas-eval' \
 *     'runMain com.netflix.atlas.eval.tools.CampaignGraphRunner \
 *        --db-path ads.db \
 *        --q "name,impressions,:eq,(,campaign_id,),:by,:sum,50e3,:2over,:gt,:vspan,40,:alpha,triggered,:legend,:rot,name,impressions,:eq,(,campaign_id,),:by,input,:legend,:rot,50e3,:const,threshold,:legend,:rot" \
 *        --s e-1w --e 2012-01-01T00:00 --tz UTC \
 *        --w 700 --h 300 --theme light \
 *        --out scripts_png_gen/output/campaign_impressions_with_alert.png'
 */
object CampaignGraphRunner {

  private case class Args(
    dbPath: String = "ads.db",
    q: String = "",
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
    debugLevel: Int = 1
  )

  def main(argv: Array[String]): Unit = {
    val args = parseArgs(argv.toList)
    if (args.isEmpty) {
      printUsage()
      sys.exit(2)
    }
    val a = args.get

    // Validate database path
    if (!java.nio.file.Files.exists(java.nio.file.Paths.get(a.dbPath))) {
      System.err.println(s"Database file not found: ${a.dbPath}")
      sys.exit(1)
    }

    // Load campaign database
    val db = new CampaignDatabase(a.dbPath, a.debugLevel)
    val uri = buildUri(a)

    val grapher = Grapher(ConfigFactory.load())
    val res = grapher.evalAndRender(uri, db)

    // Create output directory if it doesn't exist
    val out = new java.io.File(a.out)
    Option(out.getParentFile).foreach(_.mkdirs())

    // Write PNG file
    val fos = new FileOutputStream(out)
    try fos.write(res.data) finally fos.close()
    println(s"Wrote: ${out.getAbsolutePath}")

    // Optionally emit V2 GraphDef JSON (optionally gzipped)
    a.emitV2.foreach { path =>
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

  private def buildUri(a: Args): Uri = {
    import scala.collection.mutable
    val params = mutable.ListBuffer[(String, String)]()

    val q = a.style match {
      case Some(st) if st.nonEmpty => s"${a.q},:${st.toLowerCase}"
      case _                       => a.q
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

  private def parseArgs(args: List[String]): Option[Args] = {
    @annotation.tailrec
    def loop(rest: List[String], a: Args): Option[Args] = rest match {
      case Nil => if (a.q.nonEmpty && a.out.nonEmpty) Some(a) else None
      case "--db-path" :: v :: t => loop(t, a.copy(dbPath = v))
      case "--q" :: v :: t       => loop(t, a.copy(q = v))
      case "--s" :: v :: t       => loop(t, a.copy(s = Some(v)))
      case "--e" :: v :: t       => loop(t, a.copy(e = Some(v)))
      case "--tz" :: v :: t      => loop(t, a.copy(tz = Some(v)))
      case "--step" :: v :: t    => loop(t, a.copy(step = Some(v)))
      case "--no-legend" :: t    => loop(t, a.copy(noLegend = true))
      case "--theme" :: v :: t   => loop(t, a.copy(theme = Some(v)))
      case "--layout" :: v :: t  => loop(t, a.copy(layout = Some(v)))
      case "--w" :: v :: t       => loop(t, a.copy(w = Some(v.toInt)))
      case "--h" :: v :: t       => loop(t, a.copy(h = Some(v.toInt)))
      case "--palette" :: v :: t => loop(t, a.copy(palette = Some(v)))
      case "--style" :: v :: t   => loop(t, a.copy(style = Some(v)))
      case "--emit-v2" :: v :: t  => loop(t, a.copy(emitV2 = Some(v)))
      case "--save-template" :: v :: t => loop(t, a.copy(saveTemplate = Some(v)))
      case "--debug" :: v :: t => loop(t, a.copy(debugLevel = v.toInt))
      case ("--out" | "-o") :: v :: t => loop(t, a.copy(out = v))
      case _ => None
    }
    loop(args, Args())
  }

  private def printUsage(): Unit = {
    println("""
      |Usage: CampaignGraphRunner [options]
      |
      |Options:
      |  --db-path <path>     Path to SQLite database file (default: ads.db)
      |  --q <query>          Atlas StackLang query (required)
      |  --s <start>          Start time (required)
      |  --e <end>            End time (required)
      |  --tz <timezone>      Timezone (default: UTC)
      |  --step <step>        Step size
      |  --no-legend          Disable legend
      |  --theme <theme>      Chart theme (light|dark)
      |  --layout <layout>    Chart layout
      |  --w <width>          Chart width in pixels
      |  --h <height>         Chart height in pixels
      |  --palette <palette>  Color palette
      |  --style <style>      Line style (line|area|stack)
      |  --emit-v2 <path>     Emit V2 GraphDef JSON to path
      |  --save-template <path> Save args template to path
      |  --debug <level>      Debug level (1=basic, 2=detailed, 3=verbose)
      |  --out <path>         Output PNG file path (required)
      |
      |Example:
      |  CampaignGraphRunner \\
      |    --db-path ads.db \\
      |    --q "name,impressions,:eq,(,campaign_id,),:by,:sum,50e3,:2over,:gt,:vspan,40,:alpha,triggered,:legend,:rot,name,impressions,:eq,(,campaign_id,),:by,input,:legend,:rot,50e3,:const,threshold,:legend,:rot" \\
      |    --s e-1w --e 2012-01-01T00:00 --tz UTC \\
      |    --w 700 --h 300 --theme light \\
      |    --out campaign_chart.png
      |""".stripMargin)
  }

  // Helper methods from LocalGraphRunner
  private def buildGraphDefFromDb(grapher: Grapher, config: com.netflix.atlas.eval.graph.GraphConfig, db: Database): com.netflix.atlas.chart.model.GraphDef = {
    // Use the same approach as LocalGraphRunner
    val dataExprs = config.exprs.flatMap(_.expr.dataExprs).distinct
    val result: Map[com.netflix.atlas.core.model.DataExpr, List[com.netflix.atlas.core.model.TimeSeries]] = dataExprs.map { expr =>
      expr -> db.execute(config.evalContext, expr)
    }.toMap
    grapher.create(config, _.expr.eval(config.evalContext, result))
  }

  private def writeV2(path: String, gdef: com.netflix.atlas.chart.model.GraphDef): Unit = {
    val file = new java.io.File(path)
    Option(file.getParentFile).foreach(_.mkdirs())

    val json = JsonCodec.encode(gdef)
    if (path.endsWith(".gz")) {
      val fos = new FileOutputStream(file)
      val gzos = new GZIPOutputStream(fos)
      try gzos.write(json.getBytes("UTF-8")) finally gzos.close()
    } else {
      java.nio.file.Files.write(file.toPath, json.getBytes("UTF-8"))
    }
  }

  private def writeTemplate(path: String, args: Args): Unit = {
    val template = s"""
      |--db-path ${args.dbPath}
      |--q "${args.q}"
      |${args.s.map(s => s"--s $s").getOrElse("")}
      |${args.e.map(e => s"--e $e").getOrElse("")}
      |${args.tz.map(tz => s"--tz $tz").getOrElse("")}
      |${args.step.map(step => s"--step $step").getOrElse("")}
      |${if (args.noLegend) "--no-legend" else ""}
      |${args.theme.map(theme => s"--theme $theme").getOrElse("")}
      |${args.layout.map(layout => s"--layout $layout").getOrElse("")}
      |${args.w.map(w => s"--w $w").getOrElse("")}
      |${args.h.map(h => s"--h $h").getOrElse("")}
      |${args.palette.map(palette => s"--palette $palette").getOrElse("")}
      |${args.style.map(style => s"--style $style").getOrElse("")}
      |--out ${args.out}
      |${args.emitV2.map(v2 => s"--emit-v2 $v2").getOrElse("")}
      |""".stripMargin.trim

    java.nio.file.Files.write(java.nio.file.Paths.get(path), template.getBytes("UTF-8"))
  }
}
