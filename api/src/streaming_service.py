"""
Streaming service for Redpanda/Kafka integration
OOP-oriented event streaming
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError
import threading
import time

class RedpandaStreamingService:
    """OOP service for Redpanda/Kafka streaming operations"""
    
    def __init__(self,
                 bootstrap_servers: str = None,
                 region_id: str = "region-1"):
        
        self.bootstrap_servers = bootstrap_servers or os.environ.get("KAFKA_BOOTSTRAP", "localhost:9092")
        self.region_id = region_id
        self.logger = logging.getLogger("RedpandaStreamingService")
        
        # Topic names
        self.events_topic = f"{region_id}-events"
        self.chunks_topic = f"{region_id}-chunks"
        self.embeddings_topic = f"{region_id}-embeddings"
        
        # Kafka clients
        self.producer = None
        self.consumers = {}
        self.consumer_threads = {}
        self.shutdown_flag = threading.Event()
        
        self._initialize_producer()
    
    def _initialize_producer(self) -> bool:
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers.split(','),
                value_serializer=lambda v: json.dumps(v, default=str).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',
                retries=3,
                batch_size=16384,
                linger_ms=10,
                buffer_memory=33554432
            )
            
            self.logger.info(f"Kafka producer initialized: {self.bootstrap_servers}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize producer: {e}")
            return False
    
    def publish_event(self,
                     camera_id: str,
                     event_data: Dict[str, Any]) -> bool:
        """Publish event to events topic"""
        
        if not self.producer:
            self.logger.error("Producer not initialized")
            return False
        
        try:
            # Enrich event data
            enriched_event = {
                **event_data,
                "camera_id": camera_id,
                "region_id": self.region_id,
                "published_at": datetime.now().isoformat(),
                "topic": self.events_topic
            }
            
            # Send message
            future = self.producer.send(
                self.events_topic,
                key=camera_id,
                value=enriched_event
            )
            
            # Wait for confirmation
            record_metadata = future.get(timeout=10)
            
            self.logger.info(f"Published event: topic={record_metadata.topic}, "
                           f"partition={record_metadata.partition}, "
                           f"offset={record_metadata.offset}")
            return True
            
        except KafkaError as e:
            self.logger.error(f"Kafka error publishing event: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error publishing event: {e}")
            return False
    
    def publish_chunk_metadata(self,
                              camera_id: str,
                              chunk_metadata: Dict[str, Any]) -> bool:
        """Publish video chunk metadata to chunks topic"""
        
        if not self.producer:
            return False
        
        try:
            enriched_metadata = {
                **chunk_metadata,
                "camera_id": camera_id,
                "region_id": self.region_id,
                "published_at": datetime.now().isoformat(),
                "topic": self.chunks_topic
            }
            
            future = self.producer.send(
                self.chunks_topic,
                key=camera_id,
                value=enriched_metadata
            )
            
            record_metadata = future.get(timeout=10)
            
            self.logger.info(f"Published chunk metadata: offset={record_metadata.offset}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error publishing chunk metadata: {e}")
            return False
    
    def publish_embedding(self,
                         camera_id: str,
                         embedding_data: Dict[str, Any]) -> bool:
        """Publish embedding data to embeddings topic"""
        
        if not self.producer:
            return False
        
        try:
            enriched_embedding = {
                **embedding_data,
                "camera_id": camera_id,
                "region_id": self.region_id,
                "published_at": datetime.now().isoformat(),
                "topic": self.embeddings_topic
            }
            
            future = self.producer.send(
                self.embeddings_topic,
                key=camera_id,
                value=enriched_embedding
            )
            
            record_metadata = future.get(timeout=10)
            
            self.logger.info(f"Published embedding: offset={record_metadata.offset}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error publishing embedding: {e}")
            return False
    
    def create_consumer(self,
                       topics: List[str],
                       group_id: str,
                       auto_offset_reset: str = 'latest') -> Optional[KafkaConsumer]:
        """Create Kafka consumer for specified topics"""
        
        try:
            consumer = KafkaConsumer(
                *topics,
                bootstrap_servers=self.bootstrap_servers.split(','),
                group_id=group_id,
                auto_offset_reset=auto_offset_reset,
                value_deserializer=lambda m: json.loads(m.decode('utf-8')) if m else None,
                key_deserializer=lambda k: k.decode('utf-8') if k else None,
                enable_auto_commit=True,
                auto_commit_interval_ms=1000,
                session_timeout_ms=30000,
                heartbeat_interval_ms=3000
            )
            
            self.logger.info(f"Created consumer for topics: {topics}")
            return consumer
            
        except Exception as e:
            self.logger.error(f"Error creating consumer: {e}")
            return None
    
    def start_event_consumer(self,
                           group_id: str,
                           message_handler: Callable[[str, Dict[str, Any]], None]) -> bool:
        """Start consumer for events topic"""
        
        if group_id in self.consumers:
            self.logger.warning(f"Consumer {group_id} already running")
            return False
        
        try:
            consumer = self.create_consumer([self.events_topic], group_id)
            if not consumer:
                return False
            
            self.consumers[group_id] = consumer
            
            # Start consumer thread
            thread = threading.Thread(
                target=self._consume_messages,
                args=(consumer, message_handler, group_id),
                daemon=True
            )
            thread.start()
            
            self.consumer_threads[group_id] = thread
            self.logger.info(f"Started event consumer: {group_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting event consumer: {e}")
            return False
    
    def start_chunk_consumer(self,
                           group_id: str,
                           message_handler: Callable[[str, Dict[str, Any]], None]) -> bool:
        """Start consumer for chunks topic"""
        
        if group_id in self.consumers:
            return False
        
        try:
            consumer = self.create_consumer([self.chunks_topic], group_id)
            if not consumer:
                return False
            
            self.consumers[group_id] = consumer
            
            thread = threading.Thread(
                target=self._consume_messages,
                args=(consumer, message_handler, group_id),
                daemon=True
            )
            thread.start()
            
            self.consumer_threads[group_id] = thread
            self.logger.info(f"Started chunk consumer: {group_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error starting chunk consumer: {e}")
            return False
    
    def _consume_messages(self,
                         consumer: KafkaConsumer,
                         message_handler: Callable[[str, Dict[str, Any]], None],
                         group_id: str):
        """Internal method to consume messages"""
        
        self.logger.info(f"Consumer {group_id} started consuming messages")
        
        try:
            while not self.shutdown_flag.is_set():
                message_batch = consumer.poll(timeout_ms=1000)
                
                for topic_partition, messages in message_batch.items():
                    for message in messages:
                        try:
                            # Call message handler
                            message_handler(message.key, message.value)
                            
                        except Exception as e:
                            self.logger.error(f"Error processing message: {e}")
                
        except Exception as e:
            self.logger.error(f"Consumer {group_id} error: {e}")
        finally:
            consumer.close()
            self.logger.info(f"Consumer {group_id} stopped")
    
    def stop_consumer(self, group_id: str):
        """Stop specific consumer"""
        
        if group_id in self.consumers:
            consumer = self.consumers[group_id]
            consumer.close()
            del self.consumers[group_id]
            
            if group_id in self.consumer_threads:
                thread = self.consumer_threads[group_id]
                thread.join(timeout=5)
                del self.consumer_threads[group_id]
            
            self.logger.info(f"Stopped consumer: {group_id}")
    
    def stop_all_consumers(self):
        """Stop all consumers"""
        
        self.shutdown_flag.set()
        
        for group_id in list(self.consumers.keys()):
            self.stop_consumer(group_id)
        
        self.logger.info("All consumers stopped")
    
    def get_topic_info(self) -> Dict[str, Any]:
        """Get information about topics"""
        
        if not self.producer:
            return {}
        
        try:
            metadata = self.producer.cluster.bootstrap_servers[0]
            
            return {
                "bootstrap_servers": self.bootstrap_servers,
                "topics": {
                    "events": self.events_topic,
                    "chunks": self.chunks_topic,
                    "embeddings": self.embeddings_topic
                },
                "region_id": self.region_id
            }
            
        except Exception as e:
            self.logger.error(f"Error getting topic info: {e}")
            return {}
    
    def health_check(self) -> bool:
        """Check Redpanda service health"""
        
        if not self.producer:
            return False
        
        try:
            # Try to get cluster metadata
            metadata = self.producer.cluster
            return len(metadata.brokers) > 0
            
        except Exception as e:
            self.logger.error(f"Redpanda health check failed: {e}")
            return False
    
    def __del__(self):
        """Cleanup on destruction"""
        self.stop_all_consumers()
        if self.producer:
            self.producer.close()