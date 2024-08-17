import datetime
import csv

def read_input(shift_labels):
    # read input from csv file
    # csv file format: timestamp as MM/DD/YYYY HH:MM:SS string format, employee_name, availability for each day
    # output: employee_names, shift_labels, day_labels, availability
    TIMESTAMP_COL_INDEX = 0
    EMPLOYEE_NAME_COL_INDEX = 1
    AVAILABILITY_START_COL_INDEX = 2
    TIMESTAMP_FORMAT = "%m/%d/%Y %H:%M:%S"
    with open('data.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        header = next(reader) # skip header
        day_labels = header[AVAILABILITY_START_COL_INDEX:]
        # sort rows by timestamp
        rows = sorted(reader, key=lambda row: datetime.datetime.strptime(row[TIMESTAMP_COL_INDEX], TIMESTAMP_FORMAT))

        employee_names = [row[EMPLOYEE_NAME_COL_INDEX] for row in rows]
        availability = []
        for row in rows:
            employee_availability = [[] for _ in range(len(day_labels))]
            for day_index, day_availability in enumerate(row[AVAILABILITY_START_COL_INDEX:]):
                if day_availability.lower() == 'off':
                    employee_availability[day_index] = []
                elif day_availability.lower() == 'free':
                    employee_availability[day_index] = list(range(len(shift_labels)))
                else:
                    for shift in day_availability.split(","):
                        shift = shift.strip()
                        if shift in shift_labels:
                            employee_availability[day_index].append(shift_labels.index(shift))
                        else:
                            print(f"Invalid shift {shift} for employee {row[EMPLOYEE_NAME_COL_INDEX]} on day {day_labels[day_index]}")
            availability.append(employee_availability)

    # write output to csv file Employee, each day
    with open('output.csv', mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["Employee"] + day_labels)
        for employee_name, employee_availability in zip(employee_names, availability):
            writer.writerow([employee_name] + [day_availability for day_availability in employee_availability])

    return day_labels, employee_names, availability