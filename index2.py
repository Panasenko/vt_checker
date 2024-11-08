#!/bin/python3

import typer
import sys
import re
import os
import logging
from abc import ABC, abstractmethod
from dotenv import load_dotenv
#TODO: Расставить логинки по всем методам
load_dotenv()
logging.basicConfig(level=logging.ERROR)

def main(input_file: typer.FileText = typer.Argument(None, help="Входной файл (опционально)")):
    if input_file:
        scheduler(input_file.read())
    elif not sys.stdin.isatty():
        scheduler(sys.stdin.read())
    else:
        typer.echo("Не предоставлено ни файла, ни данных через stdin.")

def scheduler(content: str):
    for line in content.splitlines():
        indicator_object = Indicators(line)

        if indicator_object.get_status_valid():
            request = RequestBilder(indicator_object)
            request_object = request.get_object()

            if request_object is not None:
                print(request_object.get_url())

class Indicators:
    IP_PATTERN = r'^((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])$'
    HASH_PATTERN = r"\b([a-fA-F0-9]{32}|[a-fA-F0-9]{40}|[a-fA-F0-9]{64})\b"
    DOMAIN_PATTERN = r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'

    def __init__(self, indicator: str) -> None:
        self.indicator = indicator
        self._status_valid = False
        self._type_indicator: str

        self.valid_indicators(self.indicator)

    def get_indicator(self) -> str:
        return self.indicator

    def get_status_valid(self) -> bool:
        return self._status_valid

    def set_status_valid(self, value: bool):
        self._status_valid = value

    def get_type_indicator(self) -> str:
        return self._type_indicator

    def set_type_indicator(self, value: str):
        self._type_indicator = value

    def _validate_ip_adress(self, value) -> bool:
        return bool(re.fullmatch(self.IP_PATTERN, value))

    def _validate_hashes(self, value) -> bool:
        return bool(re.fullmatch(self.HASH_PATTERN, value))

    def _validate_domain(self, value) -> bool:
        return bool(re.fullmatch(self.DOMAIN_PATTERN, value))

    def valid_indicators(self, option: str):
        if self._validate_ip_adress(option):
            self.set_status_valid(True)
            self.set_type_indicator("ip_address")

        elif self._validate_hashes(option):
            self.set_status_valid(True)
            self.set_type_indicator("hash_file")

        elif self._validate_domain(option):
            self.set_status_valid(True)
            self.set_type_indicator("domain")
        else:
            self.set_type_indicator("no_valid")

class RequestBilder:
        def __init__(self, indicator: Indicators):
            self.indicator = indicator

        def get_object(self):
            try:
                request_object = self.RequestFactory.create_request(self.indicator)
            except ValueError as e:
                logging.error(f"Создание обьекта класса RequestFactory заверщилось ошибкой: {e}. Обработка индикатора {self.indicator.get_indicator()}")
                return None
            else:
                return request_object

        class RequestVirusTotal(ABC):

            BASE_URL_VT = os.getenv("BASE_URL_VT")
            HEADER = {
                'x-apikey': os.getenv("API_KEY"),
                'accept': 'application/json'
            }

            def __init__(self, indicator: str) -> None:
                    self.indicator = indicator

            @abstractmethod
            def get_url (self) -> str:
                pass

        class RequestHash(RequestVirusTotal):
            def __init__(self, indicator: str) -> None:
                super().__init__(indicator)
            
            def get_url(self):
                return f"{super().BASE_URL_VT}files/{self.indicator}"

        class RequestIPAdress(RequestVirusTotal):
            def __init__(self, indicator: str) -> None:
                super().__init__(indicator)

            def get_url(self):
                return f"{super().BASE_URL_VT}ip_addresses/{self.indicator}"

        class RequestDomain(RequestVirusTotal):
            def __init__(self, indicator: str) -> None:
                super().__init__(indicator)
                self.indicator = indicator

            def get_url(self):
                return f"{super().BASE_URL_VT}domains/{self.indicator}"

        class RequestFactory:
            @staticmethod
            def create_request(indicator: Indicators):
                if indicator.get_type_indicator() == "hash_file":
                    return RequestBilder.RequestHash(indicator.get_indicator())

                elif indicator.get_type_indicator() == "ip_address":
                    return RequestBilder.RequestIPAdress(indicator.get_indicator())

                elif indicator.get_type_indicator() == "domain":
                    return RequestBilder.RequestDomain(indicator.get_indicator())
                else:
                    raise ValueError("Unknown type of Indicators")

if __name__ == "__main__":
    typer.run(main)



