#!/usr/bin/env python3

from kafka import KafkaConsumer

from kafka.oauth.abstract import AbstractTokenProvider

class MyToken(AbstractTokenProvider):
    def token(self):
        return "TggqRlvEp7dKIQsz1Q/DJQp7UCchFf/JWXZtKLqu"

consumer = KafkaConsumer(bootstrap_servers='b-1-public.acceptcluster.82tzev.c5.kafka.eu-west-1.amazonaws.com:9198', security_protocol="SASL_SSL", sasl_mechanism="OAUTHBEARER", sasl_oauth_token_provider = MyToken())
for msg in consumer:
     print (msg)
