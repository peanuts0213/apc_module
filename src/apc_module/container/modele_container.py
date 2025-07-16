from dependency_injector import containers, providers

import ray.actor

from ..service.kafka_consumer import KafkaConsumer
from ..service.kafka_service import KafkaService
from ..service.module_manage_service import ModuleManageService

class ModuleContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    actors_dict = providers.Singleton(dict[int, ray.actor.ActorHandle])
    
    kafka_service = providers.Factory(
        KafkaService,
        bootstrap_servers=config.kafka.bootstrap_servers,
    )
    
    module_manage_service = providers.Factory(
        ModuleManageService,
        actors_dict = actors_dict,
        bootstrap_servers = config.kafka.bootstrap_servers,
        socketio_server_url = config.socketio_server_url,
        bottom_offset_ratio = config.bottom_offset_ratio
    )

    kafka_consumer = providers.Singleton(
        KafkaConsumer,
        kafka_service=kafka_service,
        module_manage_service=module_manage_service,
        bootstrap_servers=config.kafka.bootstrap_servers,
    )