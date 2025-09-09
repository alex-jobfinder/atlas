package com.netflix.atlas.eval.tools

import com.netflix.atlas.core.db.{Database, StaticDatabase}
import com.netflix.atlas.core.model.{DataExpr, EvalContext, TimeSeries}
import com.netflix.atlas.eval.graph.Grapher
import com.typesafe.config.{Config, ConfigFactory, ConfigValueFactory}
import org.apache.pekko.http.scaladsl.model.Uri

import java.io.FileOutputStream
import java.io.OutputStream
import java.util.zip.GZIPOutputStream
import com.netflix.atlas.chart.JsonCodec

/**
  * Render a chart from local, synthetic time series using the standard Atlas evaluator and
  * renderer. Avoids any external API or backing database.
  *
  * Examples:
  *   sbt 'project atlas-eval' \
  *     'runMain com.netflix.atlas.eval.tools.LocalGraphRunner \
  *        --preset sps \
  *        --q "name,sps,:eq,(,nf.cluster,),:by,:line" \
  *        --s e-1w --e 2012-01-01T00:00 --tz UTC \
  *        --w 700 --h 300 --theme light \
  *        --out target/manual/sps_line.png'
  */
object LocalGraphRunner {

  private case class Args(
    preset: String = "sps",
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
    style: Option[String] = None, // line | area | stack (appended to q if present)
    out: String = "",
    emitV2: Option[String] = None,
    saveTemplate: Option[String] = None
  )

  def main(argv: Array[String]): Unit = {
    val args = parseArgs(argv.toList)
    if (args.isEmpty) {
      printUsage()
      sys.exit(2)
    }
    val a = args.get

    val db = loadPresetDb(a.preset)
    val uri = buildUri(a)

    val grapher = Grapher(ConfigFactory.load())
    val res = grapher.evalAndRender(uri, db)

    val out = new java.io.File(a.out)
    Option(out.getParentFile).foreach(_.mkdirs())
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

    val query = Uri.Query(params.toList)
    Uri("http://local/api/v1/graph").withQuery(query)
  }

  // Map friendly preset names to DataSet names (see atlas-core/.../DataSet.scala)
  // DataSet.get supports: "alert" and "small". We configure StaticDatabase with that.
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
      case Nil => if (a.q.nonEmpty && a.out.nonEmpty) Some(a) else None
      case "--preset" :: v :: t => loop(t, a.copy(preset = v))
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
      case ("--out" | "-o") :: v :: t => loop(t, a.copy(out = v))
      case _ => None
    }
    loop(args, Args())
  }

  private def printUsage(): Unit = {
    val msg =
      s"""
         |Usage:
         |  runMain com.netflix.atlas.eval.tools.LocalGraphRunner --preset sps
         |    --q "name,sps,:eq,(,nf.cluster,),:by" --style line
         |    --s e-1w --e 2012-01-01T00:00 --tz UTC
         |    --w 700 --h 300 --theme light
         |    --out target/manual/sps_line.png
         |
         |Optional:
         |  --emit-v2 target/manual/sps_line.v2.json.gz   # write GraphDef (V2) alongside PNG
         |  --save-template scripts/sps_line.args         # save a reusable args file
         |
         |Notes:
         |  - --style can be: line (default), area, stack. It is appended to the ASL.
         |  - --preset maps to DataSet.scala: sps/small -> "small", alerts -> "alert".
         |  - No external API or database is used; data is provided in-process.
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
    val raw: OutputStream = new FileOutputStream(f)
    val out = if (path.toLowerCase.endsWith(".gz")) new GZIPOutputStream(raw) else raw
    try JsonCodec.encode(out, gdef) finally out.close()
  }

  /** Save a simple args template that can be reused with runMain. */
  private def writeTemplate(path: String, a: Args): Unit = {
    val parts = Seq(
      Some(s"--preset ${a.preset}"),
      Some(s"--q \"${a.q}\""),
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
      Some(s"--out ${a.out}")
    ).flatten.mkString(" ")
    val file = new java.io.File(path)
    Option(file.getParentFile).foreach(_.mkdirs())
    val content = s"# LocalGraphRunner args template\n$parts\n"
    val fos = new FileOutputStream(file)
    try fos.write(content.getBytes("UTF-8")) finally fos.close()
  }
}
