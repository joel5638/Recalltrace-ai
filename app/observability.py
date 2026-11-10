"""OpenTelemetry instrumentation, structured request logs and Prometheus metrics."""
import json,logging,os,time,uuid
from fastapi import Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

logging.basicConfig(level=os.getenv("LOG_LEVEL","INFO"),format="%(message)s")
logger=logging.getLogger("recalltrace")
REQUESTS=Counter("recalltrace_http_requests_total","HTTP requests",["method","route","status"])
LATENCY=Histogram("recalltrace_http_duration_seconds","HTTP latency",["method","route"])

def install(app):
    @app.middleware("http")
    async def observe(request:Request,call_next):
        started=time.perf_counter(); request_id=request.headers.get("x-request-id") or str(uuid.uuid4())
        try:
            response=await call_next(request)
            status=response.status_code
        except Exception:
            status=500
            raise
        finally:
            route=request.scope.get("route"); name=getattr(route,"path", "unknown")
            elapsed=time.perf_counter()-started
            REQUESTS.labels(request.method,name,str(status)).inc()
            LATENCY.labels(request.method,name).observe(elapsed)
            logger.info(json.dumps({"request_id":request_id,"method":request.method,"route":name,"status":status,"elapsed_ms":round(elapsed*1000,2)}))
        response.headers["x-request-id"]=request_id
        return response
    @app.get("/internal/metrics")
    def prometheus():
        return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)
    if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            provider=TracerProvider(); provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
            FastAPIInstrumentor.instrument_app(app,tracer_provider=provider)
        except ImportError:logger.warning("OpenTelemetry dependencies not installed")
