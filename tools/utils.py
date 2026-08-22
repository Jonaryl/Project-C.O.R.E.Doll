from datetime import datetime
import uuid
import random
import string

class Utils:
    def generate_id(self):
        new_id = ""
        time = datetime.now().strftime("%Y%m%d%H%M")

        part_a = f"{int(time)}"
        part_b = str(uuid.uuid4())
        part_c = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))

        new_id = f"{part_a}-{part_b}-{part_c}"

        #print("new_id", new_id)
        return new_id
    
    def generate_id_type2(self):
        new_id = ""
        time = datetime.now().strftime("%Y%m%d%H%M")

        part_a = f"{int(time)}"
        part_b = str(uuid.uuid4())
        part_c = ''.join(random.choice(string.ascii_letters + string.digits) for i in range(8))

        new_id = f"{part_c}-{part_b}-{part_a}"

        #print("new_id", new_id)
        return new_id

    def generate_id_number(self):
        time_part = datetime.now().strftime("%Y%m%d%H%M")
        
        random_part_b = ''.join(random.choice(string.digits) for _ in range(6))
        
        new_id = int(f"{time_part}{random_part_b}")
        
        return new_id