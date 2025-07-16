import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
import ray
from .container.modele_container import ModuleContainer

from .controller.module_manage_controller import router as module_manage_route
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    ray.shutdown()  # type:ignore
    if not ray.is_initialized(): # type:ignore
        ray.init() # type:ignore
        print("Ray initialized on startup")
    
    container = ModuleContainer()
    container.config.kafka.bootstrap_servers.from_env(
        "KAFKA_BOOTSTRAP_SERVERS", 
        "kafka:9092"
    )
    container.config.socketio_server_url.from_env(
        "SOCKET_SERVER_URL", 
        "http://human-detect-module:8000"
    )
    container.config.bottom_offset_ratio.from_env(
        "BOTTOM_OFFSET_RATIO",
        50
    )
    container.init_resources()  # type:ignore
    container.wire(
        modules=[
            ".controller.module_manage_controller"
        ]
    )
    print("Container resources initialized and wired")

    kafka_service = container.kafka_service()
    kafka_consumer = container.kafka_consumer()
    
    try:
        await kafka_service.start()
        print("✅ Kafka producer started", flush=True)
        
        await kafka_service.send("change-apc-config", "on")
        print("✅ Kafka change-apc-config topic init message sent", flush=True)

        await kafka_consumer.start()
        print("✅ Kafka consumer started and ready", flush=True)
        
        await kafka_consumer.ready_event.wait()

        await kafka_service.send("apc-module-is-on", "on")
        print("✅ Kafka is-on message sent", flush=True)

    except Exception as e:
        logger.exception(f"Kafka startup error {e}")
        
    yield  # 앱이 실행되는 동안 대기
    

    await kafka_consumer.stop()
    await kafka_service.stop()
    service = container.module_manage_service()
    for cctv_id, actor in service.actors_dict.items():
        try:
            ray.get(actor.stop.remote()) # type: ignore
            ray.kill(actor) # type: ignore
        except Exception as e:
            print(f"Failed to stop actor {cctv_id}: {e}")
    ray.shutdown() # type: ignore
    

    

# FastAPI 앱 초기화 (lifespan 전달)
app = FastAPI(
    lifespan=lifespan, 
    docs_url="/swagger-ui/index.html",
    root_path="/apc_module"
)

app.include_router(module_manage_route)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)