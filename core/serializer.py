from django.db import models
from datetime import date, datetime
from decimal import Decimal

class BaseSerializer:
    def __init__(self, queryset, date_format="%d/%m/%Y %H:%M", exclude=None):
        self.queryset = queryset
        self.date_format = date_format
        # Usamos un set para búsquedas más rápidas
        self.exclude = set(exclude or []) 

    def serialize(self):
        return [self._serialize_instance(obj) for obj in self.queryset]

    def _serialize_instance(self, obj):
        item = {}
        loaded_data = obj.__dict__
        cache = obj._state.fields_cache 

        for key, value in loaded_data.items():
            if key.startswith('_') or key in self.exclude:
                continue
            
            if key.endswith('_id'):
                field_name = key[:-3]
                # Filtro de seguridad: ¿está excluida la relación completa?
                if field_name in self.exclude:
                    continue

                if field_name in cache:
                    rel_obj = cache[field_name]
                    # Pasamos el prefijo para filtrar campos del hijo (ej: colaborador__)
                    item[field_name] = self._serialize_dict_only(rel_obj, prefix=f"{field_name}__")
                else:
                    item[key] = value
                continue

            item[key] = self._format_value(value)
        return item

    def _serialize_dict_only(self, obj, prefix=""):
        nested_item = {}
        for key, value in obj.__dict__.items():
            if key.startswith('_') or key.endswith('_cache'):
                continue
            
            # Construimos la ruta completa del campo: ej "colaborador__password"
            full_key_path = f"{prefix}{key}"
            # Limpiamos el nombre si es _id para la comparación
            clean_key_path = full_key_path[:-3] if full_key_path.endswith('_id') else full_key_path
            
            if clean_key_path in self.exclude or full_key_path in self.exclude:
                continue

            display_key = key[:-3] if key.endswith('_id') else key
            nested_item[display_key] = self._format_value(value)
            
        return nested_item

    def _format_value(self, value):
        if isinstance(value, (datetime, date)):
            return value.strftime(self.date_format)
        if isinstance(value, Decimal):
            return float(value)
        return value