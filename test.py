import heapq
import re
import sys
import csv

def binary_search(arr, target):
    left = 0
    right = len(arr) - 1
    while left <= right:
        mid = (left + right) // 2
        if arr[mid] == target:
            return mid
        if arr[mid] < target:
            left = mid + 1
        else:
            right = mid - 1
    return -1


class Employee:
    def __init__(self, id, name, availability) -> None:
        self.id = id
        self.name = name
        self.availability_in_week = availability # availability[day] = list of shifts that employee is available in that day
        self.workload = 0

    
    def is_available(self, day_index, shift_index):
        return shift_index in self.availability_in_week[day_index]


    def get_day_availability(self, day_index):
        return self.availability_in_week[day_index]
    
    
    def set_workload(self, workload):
        self.workload = workload


class Shift:
    def __init__(self, id, label, is_main_shift=True, is_even_numbered_shift=False) -> None:
        self.id = id
        self.label = label

        parts = list(map(int, re.findall(r'\d+', label)))
        self.start_time = parts[0]
        self.end_time = parts[1]
        self.workload_value = self.end_time - self.start_time

        self.is_main_shift = is_main_shift
        self.is_even_numbered_shift = is_even_numbered_shift # even numbered shifts are type of shifts that are assigned to employees on even number of days
        self.backup_shift_id = -1 # backup shift id for this shift

    def get_workload_value(self):
        return self.workload_value
    
    def set_backup(self, shift_id):
        self.backup_shift_id = shift_id

    def set_is_even_numbered_shift(self):
        self.is_even_numbered_shift = True



class EmployeeComparator:
    def __init__(self, employee, day, shift) -> None:
        self.employee = employee
        self.compared_day = day
        self.compared_shift = shift


    # compare employees
    def __lt__(self, other):
        # TODO: more criteria to prioritize employees when assigning work can be added here
        # first compare by workload
        if self.employee.workload != other.employee.workload:
            return self.employee.workload < other.employee.workload
        
        # then compare by today's availability from starting from the shift
        employee_today_availability = self.employee.get_day_availability(self.compared_day)
        other_today_availability = other.employee.get_day_availability(self.compared_day)
        employee_shift_index = binary_search(employee_today_availability, self.compared_shift)
        other_shift_index = binary_search(other_today_availability, self.compared_shift)
        employee_num_available_shifts = len(employee_today_availability) - employee_shift_index
        other_num_available_shifts = len(other_today_availability) - other_shift_index
        return employee_num_available_shifts <= other_num_available_shifts
        

class PriorityQueue:
    def __init__(self, iterable) -> None:
        self.queue = iterable
        heapq.heapify(self.queue)

    def push(self, item):
        heapq.heappush(self.queue, item)

    def pop(self):
        return heapq.heappop(self.queue)
    
    def is_empty(self):
        return len(self.queue) == 0


class Scheduler:
    def __init__(self, availability_file_path, metadata, total_workload_limit=None) -> None:
        self.day_labels, self.shift_labels = self.extract_shift_and_day_labels(availability_file_path, metadata)

        employee_names, availability = self.extract_employee_availability(availability_file_path, metadata) # index of employee_names and availability corresponds to employee_id

        self.num_employees = len(employee_names)
        self.num_days = len(self.day_labels)
        self.num_shifts = len(self.shift_labels)

        self.shifts = [Shift(i, self.shift_labels[i]) for i in range(self.num_shifts)]
        self.main_shift_ids = [shift.id for shift in self.shifts if shift.is_main_shift]
        self.covering_shifts_map = self.map_shifts_to_covering_shifts()

        
        self.employees = [Employee(i, employee_names[i], availability[i]) for i in range(self.num_employees)]
        
        self.TOTAL_WORKLOAD_LIMIT = total_workload_limit if total_workload_limit else sys.maxsize
        self.total_workload = 0
        self.WORKLOAD_LIMIT_PER_PERSON = total_workload_limit / self.num_employees if total_workload_limit else sys.maxsize
        
        self.shift_availability = self.create_shift_availability(availability)
        self.schedule = [[[] for _ in range(self.num_shifts)] for _ in range(self.num_days)] # schedule[day][shift] = [employee_id] list of employees assigned to that shift in that day
        self.assignment = [[-1 for _ in range(self.num_days)] for _ in range(self.num_employees)] # assignment[employee][day] = shift assigned to that employee in that day


    def extract_shift_and_day_labels(self, file_path, metadata):
        AVAILABILITY_START_COL_INDEX = metadata["AVAILABILITY_START_COL_INDEX"]
        DELIMITER = metadata["DELIMITER"]
        shift_labels = set()
        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=DELIMITER)
            header = next(reader)
            day_labels = header[AVAILABILITY_START_COL_INDEX:]
            rows = [row for row in reader]
            for row in rows:
                # day_availability is a string of comma separated shifts, containing the shifts that the employee is available for that day
                for day_availability in row[AVAILABILITY_START_COL_INDEX:]:
                    day_availability = day_availability.lower().strip()
                    if day_availability == 'off' or day_availability == 'free':
                        continue
                    for shift in day_availability.split(","):
                        shift_labels.add(shift.strip())
       
        # sort shift labels by start time
        START_TIME_INDEX = 0
        shift_labels = sorted(shift_labels, key=lambda shift: int(re.findall(r'\d+', shift)[START_TIME_INDEX]))
        print("Day labels:", day_labels)
        print("Shift labels:", shift_labels)
        return day_labels, shift_labels


    def extract_employee_availability(self, file_path, metadata):
        AVAILABILITY_START_COL_INDEX = metadata["AVAILABILITY_START_COL_INDEX"]
        EMPLOYEE_NAME_COL_INDEX = metadata["EMPLOYEE_NAME_COL_INDEX"]
        DELIMITER = metadata["DELIMITER"]

        with open(file_path, newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=DELIMITER)
            next(reader) # skip header
            rows = [row for row in reader]
            employee_names = [row[EMPLOYEE_NAME_COL_INDEX] for row in rows]
            availability = []
            for row in rows:
                employee_availability = [[] for _ in range(len(self.day_labels))]
                for day_index, day_availability in enumerate(row[AVAILABILITY_START_COL_INDEX:]):
                    if day_availability.lower() == 'off':
                        employee_availability[day_index] = []
                    elif day_availability.lower() == 'free':
                        employee_availability[day_index] = list(range(len(self.shift_labels)))
                    else:
                        for shift in day_availability.split(","):
                            shift = shift.strip()
                            employee_availability[day_index].append(self.shift_labels.index(shift))
                availability.append(employee_availability)
        return employee_names, availability


    def get_shift_id_by_label(self, shift_label):
        for shift in self.shifts:
            if shift.label == shift_label:
                return shift.id
        return -1
    

    def set_backup_shift(self, backup_shift_label, shift_label):
        shift_id = self.get_shift_id_by_label(shift_label)
        backup_shift_id = self.get_shift_id_by_label(backup_shift_label)
        self.get_shift(shift_id).set_backup(backup_shift_id)
        self.get_shift(backup_shift_id).is_main_shift = False
        self.main_shift_ids.remove(backup_shift_id)


    def set_even_numbered_shifts(self, shift_label):
        # even numbered shifts are type of shifts that are assigned to employees on even number of days
        shift_id = self.get_shift_id_by_label(shift_label)
        self.get_shift(shift_id).set_is_even_numbered_shift()


    def merge_overlapping_shifts(self, shifts):
        if not shifts:
            return []
        merged_shifts = [[shifts[0].start_time, shifts[0].end_time]]
        for shift in shifts[1:]:
            if shift.start_time <= merged_shifts[-1][1]:
                merged_shifts[-1][1] = max(merged_shifts[-1][1], shift.end_time)
            else:
                merged_shifts.append([shift.start_time, shift.end_time])
        return merged_shifts
    
    
    def get_employee(self, employee_id):
        return self.employees[employee_id]


    def get_shift(self, shift_id):
        return self.shifts[shift_id]


    def create_shift_availability(self, availability):
        # shift_availability[day][shift] = list of people available for that shift in that day
        shift_availability = [[[] for _ in range(self.num_shifts)] for _ in range(self.num_days)]
        for person_id, person_availability in enumerate(availability):
            # list of shifts that person is available for each day
            for day in range(self.num_days):
                for shift in person_availability[day]:
                    shift_availability[day][shift].append(person_id)
        return shift_availability

    def is_total_workload_exceeded(self, shift_index):
        shift_workload = self.get_shift(shift_index).get_workload_value()
        if self.total_workload >= self.TOTAL_WORKLOAD_LIMIT:
            return True
        if shift_workload + self.total_workload > self.TOTAL_WORKLOAD_LIMIT:
            return True
        return False
    

    def get_shifts_covering_time_range(self, start_time, end_time):
        shift_ids = []
        for shift in self.shifts:
            if shift.start_time <= start_time and shift.end_time >= end_time:
                shift_ids.append(shift.id)
            if shift.start_time >= end_time:
                break
        return shift_ids
    

    """
    Create a map of each shift to a list of shifts that have time range covering it.
    """
    def map_shifts_to_covering_shifts(self):
        shift_to_shifts_map = {}
        for shift in self.shifts:
            shift_to_shifts_map[shift.id] = self.get_shifts_covering_time_range(shift.start_time, shift.end_time)
        return shift_to_shifts_map
    

    def get_num_assignees_within_time_range(self, day_index, start_time, end_time):
        shift_ids = self.get_shifts_covering_time_range(start_time, end_time)
        num_assignees = 0
        for shift_id in shift_ids:
            num_assignees += len(self.schedule[day_index][shift_id])
        return num_assignees


    def prioritize_shifts(self, day):
        """
        Return list of shift ids in order of priority
        """
        # TODO: more criteria to prioritize shifts can be added here
        return sorted(self.main_shift_ids, key=lambda shift: len(self.shift_availability[day][shift]))
    

    def prioritize_days(self):
        # DEFAULT
        return list(range(self.num_days))


    def prioritize_employees(self, available_employee_ids, day_index, shift_index) -> PriorityQueue:
        return PriorityQueue([EmployeeComparator(self.get_employee(employee_id), day_index, shift_index) for employee_id in available_employee_ids])

    
    def get_unassigned_shifts(self, day_index):
        shifts = []
        for shift_index in self.main_shift_ids:
            backup_shift_id = self.get_shift(shift_index).backup_shift_id
            if self.schedule[day_index][shift_index] == [] and (backup_shift_id == -1 or self.schedule[day_index][backup_shift_id] == []):
                shifts.append(shift_index)
        return shifts


    def handle_special_requirement(self, day_index, special_requirement=None):
        if not special_requirement:
            return
        
        # Get the current number of assignees within the extra requirement time range
        current_num_assignees = self.get_num_assignees_within_time_range(
            day_index, 
            special_requirement["start_time"], 
            special_requirement["end_time"]
        )
        
        # Calculate the total number of assignees needed for the extra shift
        current_num_assignees_at_shift = len(self.schedule[day_index][special_requirement["shift_id_to_assign_extra"]])
        total_num_assignees_needed_for_shift = current_num_assignees_at_shift + (special_requirement["num_assignees_required"] - current_num_assignees)
        
        # Assign employees to the extra shift
        assigned = self.assign_employees_to_shift(
            day_index, 
            special_requirement["shift_id_to_assign_extra"], 
            total_num_assignees_needed_for_shift
        )
        
        # If the number of assigned employees is less than required, print a message
        if assigned < total_num_assignees_needed_for_shift:
            print(
                f"Extra requirement for day {self.day_labels[day_index]} is not met. "
                f"Required: {special_requirement['num_assignees_required']}. "
                f"Assigned: {self.get_num_assignees_within_time_range(day_index, special_requirement['start_time'], special_requirement['end_time'])}"
            )
        

    def validate_schedule(self):
        for day_index in range(self.num_days):
            unassigned_shifts = self.get_unassigned_shifts(day_index)
            for shift_index in unassigned_shifts:
                self.exchange_assignment(day_index, shift_index)
            
            # Check if the shifts are continuous within the time range of the day
            OPENING_TIME = self.shifts[0].start_time
            CLOSING_TIME = self.shifts[-1].end_time

            # Get all shifts for the given day that have assigned employees
            today_shifts = [
                self.get_shift(shift_index) 
                for shift_index in range(self.num_shifts) 
                if self.schedule[day_index][shift_index]
            ]
            merged_shifts = self.merge_overlapping_shifts(today_shifts)
            if len(merged_shifts) == 0:
                print(f"Day {self.day_labels[day_index]} has no employees.")
            else:
                if merged_shifts[0][0] > OPENING_TIME:
                    print(f"Day {self.day_labels[day_index]} has no employees during the following time ranges:")
                    print(f"{OPENING_TIME} - {merged_shifts[0][0]}")
                for i in range(len(merged_shifts) - 1):
                    print(f"Day {self.day_labels[day_index]} has no employees during the following time ranges:")
                    print(f"{merged_shifts[i][1]} - {merged_shifts[i+1][0]}")
                if merged_shifts[-1][1] < CLOSING_TIME:
                    print(f"Day {self.day_labels[day_index]} has no employees during the following time ranges:")
                    print(f"{merged_shifts[-1][1]} - {CLOSING_TIME}")
            

    def can_assign(self, employee: Employee, day_index, shift_index):
        # Retrieve the workload value of the shift
        shift_workload = self.get_shift(shift_index).get_workload_value()
        
        # Check if assigning this shift would exceed the employee's workload limit
        if employee.workload >= self.WORKLOAD_LIMIT_PER_PERSON or employee.workload + shift_workload > self.WORKLOAD_LIMIT_PER_PERSON:
            return False
        
        # Ensure the employee is not already assigned to another shift on the same day
        for shift in self.schedule[day_index]:
            if employee.id in shift:
                return False
        
        return True
    
    def put_employee_to_shift(self, employee, day_index, shift_index):
        # add employee to the shift
        self.schedule[day_index][shift_index].append(employee.id)
        self.assignment[employee.id][day_index] = shift_index

        # update  workload
        shift_workload = self.get_shift(shift_index).get_workload_value()
        self.total_workload += shift_workload
        employee.set_workload(employee.workload + shift_workload)
    

    def remove_employee_from_shift(self, employee, day_index, shift_index):
        # remove employee from the shift
        self.schedule[day_index][shift_index].remove(employee.id)
        self.assignment[employee.id][day_index] = -1

        # update workload
        shift_workload = self.get_shift(shift_index).get_workload_value()
        self.total_workload -= shift_workload
        employee.set_workload(employee.workload - shift_workload)


    def get_available_employee_ids_for_shift(self, day_index, shift_index):
        shift_ids = self.covering_shifts_map[shift_index]
        available_employee_ids = []
        for shift_id in shift_ids:
            available_employee_ids.extend(self.shift_availability[day_index][shift_id])
        return list(set(available_employee_ids))
    

    def assign_employees_to_shift(self, day_index, shift_index, to_assign=1):
        if self.is_total_workload_exceeded(shift_index):
            print(f"Total workload exceeded. Current workload: {self.total_workload}. Limit: {self.TOTAL_WORKLOAD_LIMIT}")
            return 0

        available_employee_ids = self.get_available_employee_ids_for_shift(day_index, shift_index)
        prioritized_employees = self.prioritize_employees(available_employee_ids, day_index, shift_index)
        assigned = len(self.schedule[day_index][shift_index])  # number of employees already assigned to the shift

        while not prioritized_employees.is_empty() and assigned < to_assign:
            employee = prioritized_employees.pop().employee

            if self.can_assign(employee, day_index, shift_index):
                self.put_employee_to_shift(employee, day_index, shift_index)
                assigned += 1

                handled = self.handle_even_numbered_shifts(employee, day_index, shift_index)
                if not handled:
                    self.remove_employee_from_shift(employee, day_index, shift_index)
                    assigned -= 1
                
        
        # if no one is available for the shift, look for backup shift
        if assigned < to_assign:
            backup_shift_id = self.get_shift(shift_index).backup_shift_id
            if backup_shift_id != -1:
                self.assign_employees_to_shift(day_index, backup_shift_id, to_assign)
        return assigned


    def handle_even_numbered_shifts(self, employee, day_index, shift_index):
        shift = self.get_shift(shift_index)

        # Handle even-numbered shifts
        if shift.is_even_numbered_shift:
            # Check if employee is available for another shift in the week
            if day_index == self.num_days - 1:
                return False

            available_day_ids = [
                day for day in range(day_index + 1, self.num_days)
                if shift_index in employee.availability_in_week[day] and self.can_assign(employee, day, shift_index)
            ]

            if not available_day_ids:
                return False

            second_day_id = min(available_day_ids, key=lambda day: len(self.shift_availability[day][shift_index]))
            self.put_employee_to_shift(employee, second_day_id, shift_index)
        return True

    def validate_special_requirement(self, special_requirement):
        if special_requirement:        
            # Get the shift ID for the requirement
            shift_id = self.get_shift_id_by_label(special_requirement["shift_to_assign_extra"])
            if shift_id == -1:
                raise ValueError("Invalid shift label for the extra requirement.")
            
            # Add the shift ID to the requirement
            special_requirement["shift_id_to_assign_extra"] = shift_id
        return special_requirement

    def validate_scheduling_priority(self, scheduling_priority):
        priorities = []
        for day, shift in scheduling_priority:
            if day not in self.day_labels:
                raise ValueError(f"Invalid day label: {day}")
            if shift not in self.shift_labels:
                raise ValueError(f"Invalid shift label: {shift}")
            day_index = self.day_labels.index(day)
            shift_index = self.shift_labels.index(shift)
            priorities.append((day_index, shift_index))
        return priorities
    
    def assign_work(self, scheduling_priority=None, special_requirement=None):
        special_requirement = self.validate_special_requirement(special_requirement)
        scheduling_priority = self.validate_scheduling_priority(scheduling_priority)
        for day_index, shift_index in scheduling_priority:
            self.assign_employees_to_shift(day_index, shift_index, to_assign=1)

        day_ids = self.prioritize_days()
        for day_index in day_ids:
            shift_ids = self.prioritize_shifts(day_index)
            for shift_index in shift_ids:
                self.assign_employees_to_shift(day_index, shift_index, to_assign=1)
            self.handle_special_requirement(day_index)
        self.validate_schedule()


    def exchange_assignment(self, day_index, shift_index):
        NON_EXCHANGEABLE_SHIFT = [shift.id for shift in self.shifts if shift.is_even_numbered_shift]
        if shift_index in NON_EXCHANGEABLE_SHIFT:
            return False

        # get list of employees whose workload is less than WORKLOAD_LIMIT_PER_PERSON
        under_workload_employee_ids = [employee.id for employee in self.employees if employee.workload < self.WORKLOAD_LIMIT_PER_PERSON]
        if not under_workload_employee_ids:
            return False
        
        # get list of employees available for this shift but not assigned due to workload limit
        available_employee_ids = self.get_available_employee_ids_for_shift(day_index, shift_index)
       
        # get available employees whose workload reaching WORKLOAD_LIMIT_PER_PERSON but not assigned to this shift in this day
        candidates_for_exchange = [employee_id for employee_id in available_employee_ids if self.get_employee(employee_id).workload == self.WORKLOAD_LIMIT_PER_PERSON and self.assignment[employee_id][day_index] == -1]

        if not candidates_for_exchange:
            return False
        
        for candidate_id in candidates_for_exchange:
            candidate = self.get_employee(candidate_id)
            # get candidate current assignment
            candidate_assignment = self.assignment[candidate_id] # candidate_assignment[day] = shift assigned to that employee in that day

            for day_id in range(self.num_days):
                if candidate_assignment[day_id] == -1 or candidate_assignment[day_id] in NON_EXCHANGEABLE_SHIFT:
                    continue
                assigned_shift_id = candidate_assignment[day_id]
                # under_workload employee will take the assigned shift of the candidate, so the workload of the candidate will be decreased, and the workload of the under_workload employee will be increased
                for under_workload_employee_id in under_workload_employee_ids:
                    under_workload_employee = self.get_employee(under_workload_employee_id)
                    if under_workload_employee.is_available(day_id, assigned_shift_id) and self.can_assign(under_workload_employee, day_id, assigned_shift_id):
                        # exchange the assignment
                        # remove the candidate from the assigned shift
                        self.remove_employee_from_shift(candidate, day_id, assigned_shift_id)

                        # assign the replacement employee to the assigned shift
                        self.put_employee_to_shift(under_workload_employee, day_id, assigned_shift_id)

                        # assign the candidate to the current shift
                        self.put_employee_to_shift(candidate, day_index, shift_index)
                        return True

        return False

    def get_schedule(self):
        return self.schedule
    
    def get_assignment(self):
        return self.assignment

    def write_schedule(self):
        # write schedule to csv file
        with open('schedule.csv', mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(["Shifts"] + self.day_labels)
            for shift in range(self.num_shifts):
                row = [self.shift_labels[shift]]
                for day in range(self.num_days):
                    if self.schedule[day][shift] == []:
                        row.append("None")
                    else:
                        employee_ids = self.schedule[day][shift]
                        employee_names = ", ".join([self.get_employee(employee_id).name for employee_id in employee_ids])
                        row.append(employee_names)
                writer.writerow(row)
        print ("Schedule is written to schedule.csv")

    def write_assignment(self):
        # write assignment of each employee to csv file
        with open('assignment.csv', mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(["Employee"] + self.day_labels + ["Total Workload"])
            for employee in self.employees:
                row = [employee.name]
                for day_index in range(len(self.day_labels)):
                    shift = self.assignment[employee.id][day_index]
                    if shift == -1:
                        row.append("None")
                    else:
                        row.append(self.shift_labels[shift])
                row.append(employee.workload)
                writer.writerow(row)
        print ("Assignment is written to assignment.csv")


def main():
    availability_file_path = 'data/data_31.08.24.csv'
    metadata = {
        "EMPLOYEE_NAME_COL_INDEX": 1,
        "AVAILABILITY_START_COL_INDEX": 10,
        "DELIMITER": ","
    }
    total_workload_limit = 140
    scheduler = Scheduler(availability_file_path, metadata, total_workload_limit=total_workload_limit)

    scheduler.set_backup_shift("14->18", "16->22") # 14-18 is backup for 16-22
    scheduler.set_even_numbered_shifts("16->22") # 16-22 is even numbered shift
    
    # Requirement for the number of assignees required for the time range 18:00 - 22:00 on each day
    special_requirement = {
        "start_time": 18,
        "end_time": 22,
        "num_assignees_required": 2,
        "shift_to_assign_extra": "18->22"
    }

    # Define list of tuples. Each tuple contains the day and shift to assign work first
    scheduling_priority = []

    scheduler.assign_work(scheduling_priority=scheduling_priority, special_requirement=special_requirement)

    scheduler.write_schedule()
    scheduler.write_assignment()


if __name__ == "__main__":
    main()