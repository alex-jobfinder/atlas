package com.netflix.atlas.eval.tools

import com.netflix.atlas.chart.JsonCodec
import com.netflix.atlas.core.db.{Database, StaticDatabase}
import com.netflix.atlas.core.model.{DataExpr, TimeSeries}
import com.netflix.atlas.eval.graph.Grapher
import com.typesafe.config.{Config, ConfigFactory, ConfigValueFactory}
import org.apache.pekko.actor.ActorSystem
import org.apache.pekko.http.scaladsl.Http
import org.apache.pekko.http.scaladsl.model.headers.RawHeader
import org.apache.pekko.http.scaladsl.model.{ContentTypes, HttpEntity, HttpResponse, Uri}
import org.apache.pekko.http.scaladsl.server.Directives._

import scala.concurrent.{ExecutionContextExecutor, Future}

/**
  * Minimal local HTTP server to expose GraphDef (V2 JSON) and PNG rendering for interactive use.
  *
  * Endpoints:
  *   - GET /local/graphdef?...  → returns V2 GraphDef JSON (application/json)
  *   - GET /local/png?...       → returns rendered PNG (image/png)
  *   - GET /viewer/*            → serves static files for a simple web viewer
  *
  * Query params largely match the standard /api/v1/graph API. A `style` param (line|area|stack)
  * can be provided and will be appended to the ASL expression in `q`.
  * A `preset` can be provided to choose the in-process dataset: sps|alerts|demo|range.
  */
object LocalGraphServer {

  private case class Args(
      port: Int = 9000,
      preset: String = "sps",
      viewerDir: Option[String] = None
  )

  def main(argv: Array[String]): Unit = {
    val args = parseArgs(argv.toList)
    val port = args.port
    val preset = args.preset
    val viewerDir = args.viewerDir.getOrElse("scripts_png_gen/viewer")

    implicit val system: ActorSystem = ActorSystem("local-graph-server")
    implicit val ec: ExecutionContextExecutor = system.dispatcher

    val grapher = Grapher(ConfigFactory.load())

    val route =
      respondWithHeader(RawHeader("Access-Control-Allow-Origin", "*")) {
        pathPrefix("local") {
          concat(
            path("graphdef") {
              get {
                extractRequest { req =>
                  parameters("preset".?, "style".?, Symbol("*")) { (presetOpt, styleOpt, allParams) =>
                    // Build a canonical API graph URI using incoming params, mapping style → appended ASL
                    val uri = buildApiGraphUri(req.uri, styleOpt)
                    val db = loadPresetDb(presetOpt.getOrElse(preset))
                    val gdef = buildGraphDefFromDb(grapher, uri, db)
                    val json = JsonCodec.encode(gdef)
                    complete(HttpResponse(entity = HttpEntity(ContentTypes.`application/json`, json)))
                  }
                }
              }
            },
            path("png") {
              get {
                extractRequest { req =>
                  parameters("preset".?, "style".?, Symbol("*")) { (presetOpt, styleOpt, _) =>
                    val uri = buildApiGraphUri(req.uri, styleOpt)
                    val db = loadPresetDb(presetOpt.getOrElse(preset))
                    val res = grapher.evalAndRender(uri, db)
                    complete(HttpResponse(entity = HttpEntity(ContentTypes.`image/png`, res.data)))
                  }
                }
              }
            }
          )
        } ~
        pathPrefix("viewer") {
          // Serve the static viewer assets
          getFromDirectory(viewerDir)
        }
      }

    val binding: Future[Http.ServerBinding] = Http().newServerAt("0.0.0.0", port).bind(route)
    binding.foreach { b =>
      val local = b.localAddress
      println(s"LocalGraphServer listening on http://${local.getHostString}:${local.getPort}")
      println(s"Viewer: http://localhost:${local.getPort}/viewer/")
    }
  }

  private def parseArgs(args: List[String]): Args = {
    @annotation.tailrec
    def loop(rest: List[String], a: Args): Args = rest match {
      case Nil => a
      case "--port" :: v :: t      => loop(t, a.copy(port = v.toInt))
      case "--preset" :: v :: t    => loop(t, a.copy(preset = v))
      case "--viewer-dir" :: v :: t => loop(t, a.copy(viewerDir = Some(v)))
      case _ :: t                   => loop(t, a)
    }
    loop(args, Args())
  }

  private def buildApiGraphUri(requestUri: Uri, styleOpt: Option[String]): Uri = {
    import scala.collection.mutable
    val params = mutable.ListBuffer[(String, String)]()

    val qRaw = requestUri.query().get("q").getOrElse("")
    val qWithStyle = styleOpt match {
      case Some(st) if st.nonEmpty => s"$qRaw,:${st.toLowerCase}"
      case _                       => qRaw
    }
    params += ("q" -> qWithStyle)

    def pass(k: String): Unit = requestUri.query().get(k).foreach(v => params += (k -> v))

    List("s", "e", "tz", "step", "no_legend", "theme", "layout", "w", "h", "palette").foreach(pass)

    // Preserve multi-value tz parameters
    requestUri.query().getAll("tz").drop(1).foreach(v => params += ("tz" -> v))

    val apiQuery = Uri.Query(params.toSeq: _*)
    Uri("http://local/api/v1/graph").withQuery(apiQuery)
  }

  private def loadPresetDb(name: String): Database = name.toLowerCase match {
    case "sps" | "small"   => new StaticDatabase(dbConfigWithDataset("small"))
    case "alerts" | "alert" => new StaticDatabase(dbConfigWithDataset("alert"))
    case "demo"             => StaticDatabase.demo
    case "range"            => StaticDatabase.range(1, 5)
    case other =>
      System.err.println(s"Unknown preset '$other', defaulting to 'sps'")
      new StaticDatabase(dbConfigWithDataset("small"))
  }

  private def dbConfigWithDataset(ds: String): Config = {
    val root = ConfigFactory.load()
    val base = root.getConfig("atlas.core.db")
    base.withValue("dataset", ConfigValueFactory.fromAnyRef(ds))
  }

  private def buildGraphDefFromDb(grapher: Grapher, uri: Uri, db: Database) = {
    val config = grapher.toGraphConfig(uri)
    val dataExprs = config.exprs.flatMap(_.expr.dataExprs).distinct
    val result: Map[DataExpr, List[TimeSeries]] = dataExprs.map { expr =>
      expr -> db.execute(config.evalContext, expr)
    }.toMap
    grapher.create(config, _.expr.eval(config.evalContext, result))
  }
}


