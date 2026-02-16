from django.db import models
from datetime import date, datetime
from decimal import Decimal

class BaseSerializer:
    def __init__(self, queryset, date_format="%d/%m/%Y %H:%M"):
        self.queryset = queryset
        self.date_format = date_format

    def serialize(self):
        return [self._serialize_instance(obj) for obj in self.queryset]

    def _serialize_instance(self, obj):
        item = {}
        # Datos cargados en el objeto principal
        loaded_data = obj.__dict__
        # Cache de objetos relacionados (select_related)
        cache = obj._state.fields_cache 

        for key, value in loaded_data.items():
            if key.startswith('_'):
                continue
            
            if key.endswith('_id'):
                field_name = key[:-3]
                # Si el objeto relacionado está en memoria, lo serializamos
                if field_name in cache:
                    rel_obj = cache[field_name]
                    # Aquí está el cambio: serializamos solo lo cargado en el anidado
                    item[field_name] = self._serialize_dict_only(rel_obj)
                else:
                    item[key] = value
                continue

            item[key] = self._format_value(value)
        return item

    def _serialize_dict_only(self, obj):
        """
        Serializa ÚNICAMENTE lo que esté cargado en el __dict__ del objeto relacionado.
        Esto respeta estrictamente el .only()
        """
        nested_item = {}
        for key, value in obj.__dict__.items():
            # Saltamos estados internos y campos que son otros objetos (evitar recursión)
            if key.startswith('_') or key.endswith('_cache'):
                continue
            
            # Limpiamos el nombre si es un _id
            display_key = key[:-3] if key.endswith('_id') else key
            nested_item[display_key] = self._format_value(value)
            
        return nested_item

    def _format_value(self, value):
        if isinstance(value, (datetime, date)):
            return value.strftime(self.date_format)
        if isinstance(value, Decimal):
            return float(value)
        return value