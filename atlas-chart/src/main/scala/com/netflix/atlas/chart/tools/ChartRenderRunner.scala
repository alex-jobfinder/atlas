/*
 * Lightweight runner to render a PNG chart from a graph JSON file.
 * Supports:
 *   - V1 API JSON (as used by test resources like default_non_uniformly_drawn_spikes.json)
 *   - V2 JsonCodec JSON (optionally .gz compressed)
 */
package com.netflix.atlas.chart.tools

import java.io.{BufferedInputStream, File, FileInputStream, FileOutputStream, InputStream}
import java.time.Instant
import java.util.zip.GZIPInputStream

import com.netflix.atlas.chart.{DefaultGraphEngine, JsonCodec}
import com.netflix.atlas.chart.model.{GraphDef, LineDef, PlotDef}
import com.netflix.atlas.core.model.{ArrayTimeSeq, DsType, TimeSeries}
import com.netflix.atlas.json.Json

import scala.util.Using

object ChartRenderRunner {

  private sealed trait Format
  private case object V1 extends Format // API style graph JSON used in older samples
  private case object V2 extends Format // JsonCodec format supported by atlas-chart

  def main(args: Array[String]): Unit = {
    val parsed = parseArgs(args.toList)
    if (parsed.isEmpty) {
      printUsage()
      sys.exit(2)
    }
    val (inPath, outPath, fmtOpt, themeOpt, both) = parsed.get

    val format = fmtOpt.getOrElse(detectFormat(inPath))
    val baseGraph = loadGraphDef(inPath, format)

    val engine = new DefaultGraphEngine
    if (both) {
      val base = deriveBase(outPath, inPath)
      val lightOut = new File(s"${base}.png")
      val darkOut = new File(s"${base}_dark.png")
      write(engine, applyTheme(baseGraph, Some("light")), lightOut)
      write(engine, applyTheme(baseGraph, Some("dark")), darkOut)
    } else {
      val themed = applyTheme(baseGraph, themeOpt)
      val outFile = new File(outPath.getOrElse(defaultOut(inPath)))
      write(engine, themed, outFile)
    }
  }

  private def defaultOut(inPath: String): String = {
    val f = new File(inPath).getName
    val base = f.replaceAll("(?i)\\.json(\\.gz)?$", "")
    s"target/manual/${base}.png"
  }

  private def deriveBase(outPath: Option[String], inPath: String): String = {
    val provided = outPath.getOrElse(defaultOut(inPath))
    if (provided.toLowerCase.endsWith(".png")) provided.dropRight(4) else provided
  }

  private def parseArgs(args: List[String]): Option[(String, Option[String], Option[Format], Option[String], Boolean)] = {
    @annotation.tailrec
    def loop(rest: List[String], in: Option[String], out: Option[String], fmt: Option[Format], theme: Option[String], both: Boolean): Option[(String, Option[String], Option[Format], Option[String], Boolean)] =
      rest match {
        case Nil => in.map((_, out, fmt, theme, both))
        case ("--input" | "-i") :: v :: t => loop(t, Some(v), out, fmt, theme, both)
        case ("--output" | "-o") :: v :: t => loop(t, in, Some(v), fmt, theme, both)
        case "--format" :: v :: t =>
          val f = v.toLowerCase match {
            case "v1" => Some(V1)
            case "v2" => Some(V2)
            case _     => None
          }
          if (f.isEmpty) return None else loop(t, in, out, f, theme, both)
        case "--theme" :: v :: t =>
          val th = v.toLowerCase match {
            case "light" => Some("light")
            case "dark"  => Some("dark")
            case _        => None
          }
          if (th.isEmpty) return None else loop(t, in, out, fmt, th, both)
        case "--both" :: t => loop(t, in, out, fmt, None, true)
        case _ => return None
      }
    loop(args, None, None, None, None, false)
  }

  private def printUsage(): Unit = {
    val msg =
      """
         |Usage:
         |  runMain com.netflix.atlas.chart.tools.ChartRenderRunner --input <graph.json[.gz]> [--output out.png] [--format v1|v2] [--theme light|dark] [--both]
         |
         |Examples:
         |  # Render V1 API-style JSON bundled with tests
         |  sbt 'project atlas-chart' 'runMain com.netflix.atlas.chart.tools.ChartRenderRunner --input atlas-chart/src/test/resources/graphengine/data/default_non_uniformly_drawn_spikes.json --output target/manual/default_non_uniformly_drawn_spikes.png'
         |
         |  # Render V2 JsonCodec JSON (plain or .gz)
         |  sbt 'project atlas-chart' 'runMain com.netflix.atlas.chart.tools.ChartRenderRunner --input <path-to-json-or-json.gz> --format v2 --theme dark'
         |
         |  # Render both light and dark variants (out.png and out_dark.png)
         |  sbt 'project atlas-chart' 'runMain com.netflix.atlas.chart.tools.ChartRenderRunner --input ... --output out.png --both'
         |""".stripMargin
    System.err.println(msg)
  }

  private def detectFormat(path: String): Format = {
    val p = path.toLowerCase
    if (p.endsWith(".json.gz")) V2 else V1
  }

  private def open(path: String): InputStream =
    new BufferedInputStream(new FileInputStream(path))

  private def loadGraphDef(path: String, format: Format): GraphDef = format match {
    case V2 =>
      val p = path.toLowerCase
      val in = if (p.endsWith(".gz")) new GZIPInputStream(open(path)) else open(path)
      Using.resource(in)(JsonCodec.decode)
    case V1 =>
      Using.resource(open(path)) { in =>
        Json.decode[GraphData](in).toGraphDef
      }
  }

  // Minimal V1 data model and converter copied from test style
  private case class GraphData(
      start: Long,
      step: Long,
      legend: List[String],
      metrics: List[Map[String, String]],
      values: List[List[Double]]
  ) {
    def toGraphDef: GraphDef = {
      val nbrSteps = math.max(0, values.length - 1)
      val s = Instant.ofEpochMilli(start)
      val e = s.plusMillis(step * nbrSteps)
      val seq = new ArrayTimeSeq(DsType.Gauge, s.toEpochMilli, step, values.flatten.toArray)
      val seriesDef = LineDef(TimeSeries(Map.empty, "0", seq))
      val plotDef = PlotDef(List(seriesDef))
      GraphDef(startTime = s, endTime = e, step = step, plots = List(plotDef))
    }
  }

  private def applyTheme(g: GraphDef, theme: Option[String]): GraphDef = theme match {
    case Some("dark")  => g.copy(themeName = "dark")
    case Some("light") => g.copy(themeName = "light")
    case _              => g
  }

  private def write(engine: DefaultGraphEngine, graphDef: GraphDef, outFile: File): Unit = {
    outFile.getParentFile match {
      case null => // ok
      case d if !d.exists() => d.mkdirs()
      case _ =>
    }
    Using.resource(new FileOutputStream(outFile)) { out =>
      engine.write(graphDef, out)
    }
    println(s"Wrote PNG: ${outFile.getAbsolutePath}")
  }
}
