from datetime import datetime, date, timedelta


data = date.today()
print(data)

old_data = data - timedelta(7)
print(old_data)