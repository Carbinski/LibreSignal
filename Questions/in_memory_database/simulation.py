from dataclasses import dataclass, field
import copy

@dataclass
class Record:
    id: str
    fields: dict = field(default_factory=dict)

@dataclass
class Field:
    field: str
    value: str
    timestamp: int
    ttl: int

class InMemoryDatabase:
    def __init__(self):
        self.records = {}
        self.backups = []
    
    # ========== Level 1 Operations ==========
    def set(self, key, field, value):
        return self.set_at_with_ttl(key, field, value, timestamp=-1, ttl=-1)
    
    def get(self, key, field):
        return self.get_at(key, field, -1)

    def delete(self, key, field):
        if key not in self.records or field not in self.records[key].fields:
            return "false"
        record = self.records[key]
        del record.fields[field]
        return "true"
    
    # ========== Level 2 Operations ==========
    def scan(self, key):
        return self.scan_at(key, -1)
        

    def scan_by_prefix(self, key, prefix):
        return self.scan_by_prefix_at(key, prefix, -1)


    def get_record_string(self, map, function):
        output = []
        for key, value in map.items():
            output.append(f"{key}({value})")
        output.sort()
        return ", ".join(output)

    # ========== Level 3 Operations ==========
    def is_valid_timestamp(self, timestamp, ttl_field):
        if ttl_field.ttl == -1:
            return True
        if timestamp < ttl_field.timestamp + ttl_field.ttl:
            return True
        return False

    def set_at(self, key, field, value, timestamp):
        return self.set_at_with_ttl(key, field, value, timestamp, -1)

    def set_at_with_ttl(self, key, field, value, timestamp, ttl):
        ttl_field = Field(field, value, timestamp, ttl)
        if key not in self.records:
            self.records[key] = Record(id=key, fields={field:ttl_field})
        elif field not in self.records[key].fields:
            record = self.records[key]
            record.fields[field] = ttl_field
        else:
            self.records[key].fields[field] = ttl_field
        return ""

    def delete_at(self, key, field, timestamp):
        if key not in self.records or field not in self.records[key].fields:
            return "false"
        record = self.records[key]
        ttl_field = record.fields[field]
        del record.fields[field]

        if not self.is_valid_timestamp(timestamp, ttl_field):
            return "false"
        return "true"

    def get_at(self, key, field, timestamp):
        if key not in self.records or field not in self.records[key].fields:
            return ""
        
        record = self.records[key]
        ttl_field = record.fields[field]
        if not self.is_valid_timestamp(timestamp, ttl_field):
            del record.fields[field]
            return ""
        return ttl_field.value

    def scan_at(self, key, timestamp):
        if key not in self.records:
            return ""
        else:
            output = []
            for field, field_data in self.records[key].fields.items():
                if self.is_valid_timestamp(timestamp, field_data):
                    output.append(f"{field}({field_data.value})")
            output.sort()
            return ", ".join(output)

    def scan_by_prefix_at(self, key, prefix, timestamp):
        if key not in self.records:
            return ""
        else:
            output = []
            for field, field_data in self.records[key].fields.items():
                if field.startswith(prefix) and self.is_valid_timestamp(timestamp, field_data):
                    output.append(f"{field}({field_data.value})")
            output.sort()
            return ", ".join(output)

    # ========== Level 4 Operations ==========
    def update_records(self, timestamp):
        records_to_remove = []
        for record_key, record in self.records.items():
            elements_to_remove = []
            for key, value in record.fields.items():
                if value.timestamp + value.ttl < timestamp and value.ttl != -1:
                    elements_to_remove.append(key)
            for element in elements_to_remove:
                del record.fields[element]
                if not record.fields:
                    records_to_remove.append(record_key)
        for key in records_to_remove:
            del self.records[key]

            

    def backup(self, timestamp):
        self.update_records(timestamp)
        self.backups.append([timestamp, copy.deepcopy(self.records)])
        return str(len(self.records))

    def restore(self, timestamp, timestampToRestore):
        latest_backup = None
        for backup in self.backups:
            if backup[0] < timestampToRestore:
                latest_backup = backup
            else:
                break

        self.records = latest_backup[1]
        backup_timestamp = latest_backup[0]

        for record in self.records.values():
            for data_field in record.fields.values():
                if data_field.ttl != -1:
                    data_field.ttl += timestamp - backup_timestamp

                