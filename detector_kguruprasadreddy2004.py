
import csv
import json
import re
import sys

class PIIDetector:
    def __init__(self):
        # took me a while to get these patterns right - lots of trial and error!
        self.phone_regex = re.compile(r'\b\d{10}\b')  # simple 10 digit check
        self.aadhar_regex = re.compile(r'\b\d{12}\b|\b\d{4}\s\d{4}\s\d{4}\b')  # 12 digits with/without spaces
        self.passport_regex = re.compile(r'\b[A-Z]\d{7}\b')  # letter + 7 digits seems common
        self.upi_regex = re.compile(r'\w+@\w+')  # basic upi format

        # for emails and names - these were tricky to get right
        self.email_regex = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        self.full_name_regex = re.compile(r'^[A-Z][a-z]+ [A-Z][a-z]+')  # first + last name
        self.address_regex = re.compile(r'.+,.*,.*\d{6}')  # street, city, pincode pattern
        self.ip_regex = re.compile(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}')

        # fields that count as PII when combined
        self.combo_fields = ['name', 'email', 'address', 'device_id', 'ip_address']
        
    def check_standalone_pii(self, field_name, field_value):
        # check if this field by itself is PII
        val = str(field_value)

        if field_name == 'phone':
            return bool(self.phone_regex.match(val))
        elif field_name == 'aadhar':
            return bool(self.aadhar_regex.match(val))
        elif field_name == 'passport':
            return bool(self.passport_regex.match(val))
        elif field_name == 'upi_id':
            return bool(self.upi_regex.search(val))

        return False
    
    def looks_like_name(self, val):
        # check if it's a proper full name
        return bool(self.full_name_regex.match(str(val)))

    def looks_like_email(self, val):
        return bool(self.email_regex.match(str(val)))

    def looks_like_address(self, val):
        # addresses usually have commas and a pincode at the end
        return bool(self.address_regex.search(str(val)))

    def looks_like_device_id(self, val):
        # device IDs are usually alphanumeric and reasonably long
        val_str = str(val)
        return len(val_str) >= 6 and val_str.isalnum()

    def looks_like_ip(self, val):
        return bool(self.ip_regex.match(str(val)))
    
    def find_combo_pii(self, record_data):
        # look for combinations of fields that together make PII
        found_fields = []

        for field_name, field_value in record_data.items():
            if field_name == 'name' and self.looks_like_name(field_value):
                found_fields.append(field_name)
            elif field_name == 'email' and self.looks_like_email(field_value):
                found_fields.append(field_name)
            elif field_name == 'address' and self.looks_like_address(field_value):
                found_fields.append(field_name)
            elif field_name == 'device_id' and self.looks_like_device_id(field_value):
                found_fields.append(field_name)
            elif field_name == 'ip_address' and self.looks_like_ip(field_value):
                found_fields.append(field_name)

        # need at least 2 fields to be PII
        is_pii = len(found_fields) >= 2
        return is_pii, found_fields
    
    def mask_phone(self, phone_num):
        # keep first 2 and last 2 digits visible
        p = str(phone_num)
        if len(p) == 10:
            return p[:2] + "XXXXXX" + p[-2:]
        return "[REDACTED_PHONE]"

    def mask_aadhar(self, aadhar_num):
        # remove spaces and keep first 4 and last 4
        clean = str(aadhar_num).replace(' ', '')
        if len(clean) == 12:
            return clean[:4] + "XXXX" + clean[-4:]
        return "[REDACTED_AADHAR]"

    def mask_passport(self, passport_num):
        return "[REDACTED_PASSPORT]"

    def mask_upi(self, upi_id):
        return "[REDACTED_UPI]"

    def mask_name(self, full_name):
        # keep first letter of each word
        words = str(full_name).split()
        masked = []
        for word in words:
            if len(word) > 0:
                masked.append(word[0] + 'X' * (len(word) - 1))
        return " ".join(masked)

    def mask_email(self, email_addr):
        # keep first 2 chars and domain
        email_str = str(email_addr)
        if '@' in email_str:
            username, domain = email_str.split('@', 1)
            if len(username) > 2:
                masked_user = username[:2] + 'X' * (len(username) - 2)
            else:
                masked_user = 'XX'
            return masked_user + '@' + domain
        return "[REDACTED_EMAIL]"

    def mask_address(self, addr):
        return "[REDACTED_ADDRESS]"

    def mask_device_id(self, dev_id):
        return "[REDACTED_DEVICE_ID]"

    def mask_ip_address(self, ip_addr):
        return "[REDACTED_IP]"
    
    def analyze_record(self, data):
        # main function to check if record has PII and redact it
        result_data = data.copy()
        found_pii = False

        # first check standalone PII fields
        for field_name, field_value in data.items():
            if self.check_standalone_pii(field_name, field_value):
                found_pii = True

                # mask the value based on type
                if field_name == 'phone':
                    result_data[field_name] = self.mask_phone(field_value)
                elif field_name == 'aadhar':
                    result_data[field_name] = self.mask_aadhar(field_value)
                elif field_name == 'passport':
                    result_data[field_name] = self.mask_passport(field_value)
                elif field_name == 'upi_id':
                    result_data[field_name] = self.mask_upi(field_value)

        # then check combinatorial PII
        has_combo_pii, combo_fields = self.find_combo_pii(data)

        if has_combo_pii:
            found_pii = True

            # mask all the combo fields
            for field_name in combo_fields:
                field_value = data[field_name]
                if field_name == 'name':
                    result_data[field_name] = self.mask_name(field_value)
                elif field_name == 'email':
                    result_data[field_name] = self.mask_email(field_value)
                elif field_name == 'address':
                    result_data[field_name] = self.mask_address(field_value)
                elif field_name == 'device_id':
                    result_data[field_name] = self.mask_device_id(field_value)
                elif field_name == 'ip_address':
                    result_data[field_name] = self.mask_ip_address(field_value)

        return result_data, found_pii


# main execution function
def run_detector():
    if len(sys.argv) != 2:
        print("Usage: python3 detector_full_kguruprasadreddy2004.py <input_csv_file>")
        return

    input_filename = sys.argv[1]
    output_filename = "redacted_output_kguruprasadreddy2004.csv"

    # create the detector instance
    pii_detector = PIIDetector()

    try:
        # open files for reading and writing
        with open(input_filename, 'r') as input_file, open(output_filename, 'w', newline='') as output_file:
            csv_reader = csv.DictReader(input_file)
            csv_writer = csv.writer(output_file)

            # write the header row
            csv_writer.writerow(['record_id', 'redacted_data_json', 'is_pii'])

            # process each row
            for row in csv_reader:
                rec_id = row['record_id']
                json_data = row['data_json']

                try:
                    # sometimes the JSON has extra quotes - need to clean it
                    clean_json = json_data.strip()
                    if clean_json.endswith('""'):
                        clean_json = clean_json[:-1]

                    # parse the JSON
                    parsed_data = json.loads(clean_json)

                    # run PII detection and redaction
                    redacted_data, has_pii = pii_detector.analyze_record(parsed_data)

                    # convert back to JSON string
                    output_json = json.dumps(redacted_data, separators=(',', ': '))

                    # write the result
                    csv_writer.writerow([rec_id, output_json, has_pii])

                except json.JSONDecodeError as json_err:
                    print(f"Error parsing JSON in record {rec_id}: {json_err}")
                    # try to fix some common JSON issues
                    try:
                        fixed_json = json_data.strip().strip('"')
                        # fix unquoted dates
                        if ': 2024-' in fixed_json and '"2024-' not in fixed_json:
                            fixed_json = re.sub(r': (2024-\d{2}-\d{2})', r': "\1"', fixed_json)
                        parsed_data = json.loads(fixed_json)
                        redacted_data, has_pii = pii_detector.analyze_record(parsed_data)
                        output_json = json.dumps(redacted_data, separators=(',', ': '))
                        csv_writer.writerow([rec_id, output_json, has_pii])
                    except:
                        # if all else fails, just copy the original
                        csv_writer.writerow([rec_id, json_data, False])
                except Exception as other_err:
                    print(f"Error processing record {rec_id}: {other_err}")
                    csv_writer.writerow([rec_id, json_data, False])

    except FileNotFoundError:
        print(f"Could not find input file: {input_filename}")
    except Exception as err:
        print(f"Unexpected error: {err}")

    print(f"Done! Check {output_filename} for results")


if __name__ == "__main__":
    run_detector()
