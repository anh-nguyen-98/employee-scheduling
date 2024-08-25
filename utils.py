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
    with open('data_1.csv', newline='') as csvfile:
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

def write_schedule(day_labels, shift_labels, schedule, employees):
    num_days = len(day_labels)
    num_shifts = len(shift_labels)
    # write schedule to csv file
    with open('schedule.csv', mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["Shifts"] + day_labels)
        for shift in range(num_shifts):
            row = [shift_labels[shift]]
            for day in range(num_days):
                if schedule[day][shift] == []:
                    row.append("None")
                else:
                    employee_ids = schedule[day][shift]
                    employee_names = ", ".join([employees[employee_id].name for employee_id in employee_ids])
                    row.append(employee_names)
            writer.writerow(row)
    print ("Schedule is written to schedule.csv")

def write_assignment(day_labels, shift_labels, assignment, employees):
    # write assignment of each employee to csv file
    with open('assignment.csv', mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(["Employee"] + day_labels + ["Total Workload"])
        for employee in employees:
            row = [employee.name]
            for day_index in range(len(day_labels)):
                shift = assignment[employee.id][day_index]
                if shift == -1:
                    row.append("None")
                else:
                    row.append(shift_labels[shift])
            row.append(employee.workload)
            writer.writerow(row)
    print ("Assignment is written to assignment.csv")