import uuid
from aiokafka import AIOKafkaConsumer #type: ignore
import asyncio
from ..dto.kafka.consumer.change_apc_data_dto import ChangeApcDataDto
from .kafka_service import KafkaService
from .module_manage_service import ModuleManageService

class KafkaConsumer:
    def __init__(
        self,
        bootstrap_servers: str,
        kafka_service: KafkaService,
        module_manage_service: ModuleManageService
    ):
        self.kafka_service = kafka_service
        self.bootstrap_servers = bootstrap_servers
        self.module_manage_service = module_manage_service

        self.tasks:list[asyncio.Task[None]] = []
        self.consumers: list[AIOKafkaConsumer] = []
        self.running = False
        self.ready_event = asyncio.Event()

    async def start(self):
        self.running = True
        await self.set_consumer_group()  # 🔄 직접 await

    async def stop(self):
        self.running = False
        for consumer in self.consumers:
            await consumer.stop()  # type: ignore

        for task in self.tasks:  # type: ignore
            task.cancel()
        await asyncio.gather(*self.tasks, return_exceptions=True)

    async def set_consumer_group(self):
        try:
            consumer = AIOKafkaConsumer(
                bootstrap_servers=self.bootstrap_servers,
                group_id=f"apc_module_{uuid.uuid4()}",  # ✅ 다시 랜덤 group_id 사용
                auto_offset_reset="latest",
                value_deserializer=lambda v: self._safe_deserialize(  # type: ignore
                    ChangeApcDataDto,
                    v  # type: ignore
                )
            )
        except Exception as e:
            print(f"AIOKafkaConsumer init error: {e}", flush=True)
            return

        await self._start_consumer(consumer)
        self.consumers.append(consumer)

        # consume task는 백그라운드에서 처리
        task = asyncio.create_task(self._consume_messages(consumer))
        self.tasks.append(task)

    async def _start_consumer(self, consumer: AIOKafkaConsumer):
        try:
            await asyncio.wait_for(consumer.start(), timeout=10.0)
            consumer.subscribe(["change-apc-config"]) # type: ignore
            print("✅ Subscribed to topic.", flush=True)
            
            await asyncio.sleep(3)
            self.ready_event.set()
            print("✅ ready_event.set() called.", flush=True)
            
        except asyncio.TimeoutError:
            print("Consumer start timed out after 10 seconds", flush=True)
        except Exception as e:
            print(f"Consumer start/subscribe error: {e}", flush=True)

    async def _consume_messages(self, consumer: AIOKafkaConsumer):
        while not consumer.assignment() and self.running:
            await asyncio.sleep(1)
        if not self.running:
            return
        try:
            async for msg in consumer: # type: ignore
                try:
                    print(f"{msg}", flush=True)
                except Exception as e:
                    print(f"Error in handler: {e}", flush=True)
                if msg.value: # type: ignore
                    try:
                        await self.module_manage_service.apply_apc_data(msg.value) # type: ignore
                    except Exception as e:
                        print(f"Error in handler: {e}", flush=True)
        except asyncio.CancelledError:
            print("asyncio.CancelledError", flush=True)
            pass

    def _safe_deserialize(
        self,
        model_class: type[ChangeApcDataDto],
        value_bytes: bytes
    ):
        try:
            json_str = value_bytes.decode()
            print("RAW MESSAGE STRING:", json_str[:300], flush=True)
            return model_class.model_validate_json(json_str)
        except Exception as e:
            print(f"Deserialization failed: {e}")
            return None
