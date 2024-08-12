import heapq
import math
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
    def __init__(self, id, name, registration_time, availability) -> None:
        self.id = id
        self.name = name
        self.availability_in_week = availability # availability[day] = list of shifts that employee is available in that day
        self.workload = 0
        self.registration_time = registration_time

    def get_availability_on_day(self, day):
        return self.availability_in_week[day]
    
    
    def set_workload(self, workload):
        self.workload = workload


class Shift:
    def __init__(self, id, label, is_main_shift=True) -> None:
        self.id = id
        self.label = label
        self.is_main_shift = is_main_shift
        self.backup_shift = None

    def get_workload_value(self):
        # workload value can be adjusted here
        return 1
    
    def set_backup(self, shift):
        self.backup_shift = shift


class TimeRangeShift(Shift):
    def __init__(self, id, label) -> None:
        super().__init__(id, label)
        parts = list(map(int, label.split("-")))
        self.start_time = parts[0]
        self.end_time = parts[1]

    
    def get_workload_value(self):
        return self.end_time - self.start_time
        
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
        employee_today_availability = self.employee.get_availability_on_day(self.compared_day)
        other_today_availability = other.employee.get_availability_on_day(self.compared_day)
        employee_shift_index = binary_search(employee_today_availability, self.compared_shift)
        other_shift_index = binary_search(other_today_availability, self.compared_shift)
        employee_num_available_shifts = len(employee_today_availability) - employee_shift_index
        other_num_available_shifts = len(other_today_availability) - other_shift_index
        if employee_num_available_shifts != other_num_available_shifts:
            return len(employee_today_availability) < len(other_today_availability)
        
        # then compare by registration time   
        return self.employee.registration_time < other.employee.registration_time
        

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
    def __init__(self, availability, employee_names, day_labels, shift_labels, work_limit=None) -> None:
        self.day_labels = day_labels
        self.shift_labels = shift_labels
        self.num_employees = len(employee_names)
        self.num_days = len(day_labels)
        self.num_shifts = len(shift_labels)

        self.employees = [Employee(i, employee_names[i], i, availability[i]) for i in range(self.num_employees)]
        self.shifts = [TimeRangeShift(i, shift_labels[i]) for i in range(self.num_shifts)]
        self.shifts = sorted(self.shifts, key=lambda shift: shift.start_time)

        ### EDIT LATER
        self.get_shift(2).is_main_shift = False # 14-18 is not a main shift
        self.get_shift(3).set_backup(self.get_shift(2)) # 14-18 is backup for 16-22
        ###

        self.shift_availability = self.create_shift_availability(availability)

        self.WORKLOAD_LIMIT_PER_PERSON = self.calculate_workload_limit() if work_limit is None else work_limit

        self.schedule = [[[] for _ in range(self.num_shifts)] for _ in range(self.num_days)] # schedule[day][shift] = [employee_id] list of employees assigned to that shift in that day


    @staticmethod
    def are_shifts_continuous_within_range(shifts, start_time, end_time):
        if len(shifts) == 0 or shifts[0].start_time > start_time:
            return False
        max_finish_time = shifts[0].end_time
        for shift in shifts[1:]:
            if shift.start_time > max_finish_time:
                return False
            max_finish_time = max(max_finish_time, shift.end_time)
        return max_finish_time >= end_time
    

    def get_employee(self, employee_id):
        return self.employees[employee_id]


    def get_shift(self, shift_id):
        return self.shifts[shift_id]


    def calculate_workload_limit(self):
        # TODO: workload limit can be adjusted here
        return math.ceil(self.num_days * self.num_shifts / self.num_employees)


    def create_shift_availability(self, availability):
        # shift_availability[day][shift] = list of people available for that shift in that day
        shift_availability = [[[] for _ in range(self.num_shifts)] for _ in range(self.num_days)]
        for person_id, person_availability in enumerate(availability):
            # list of shifts that person is available for each day
            for day in range(self.num_days):
                for shift in person_availability[day]:
                    shift_availability[day][shift].append(person_id)
        return shift_availability


    def can_assign(self, employee, day, shift):
        # MORE CONDITIONS CAN BE ADDED HERE
        if employee.workload >= self.WORKLOAD_LIMIT_PER_PERSON:
            return False
        for shift in self.schedule[day]:
            if employee.id in shift:
                return False
        return True
    
    def get_shifts_within_range(self, start_time, end_time):
        return [shift.id for shift in self.shifts if shift.start_time <= start_time and shift.end_time >= end_time]
    
    def get_available_employee_ids_for_shift(self, day, shift):
        shifts = self.get_shifts_within_range(self.get_shift(shift).start_time, self.get_shift(shift).end_time)
        available_employee_ids = set()
        for shift in shifts:
            available_employee_ids.update(self.shift_availability[day][shift])
        return list(available_employee_ids)

    def get_num_assignees_within_range(self, day, start_time, end_time):
        shifts = self.get_shifts_within_range(start_time, end_time)
        num_assignees = 0
        for shift in shifts:
            num_assignees += len(self.schedule[day][shift])
        return num_assignees

    def prioritize_shifts(self, day):
        # sort shifts by number of available people in that day
        # TODO: more criteria to prioritize shifts can be added here
        # shifts = sorted(range(self.num_shifts), key=lambda shift: len(self.shift_availability[day][shift]))
        shifts = [shift for shift in list(range(self.num_shifts)) if self.get_shift(shift).is_main_shift]
        return shifts


    def prioritize_employees(self, available_employee_ids, day, shift):
        return PriorityQueue([EmployeeComparator(self.get_employee(employee_id), day, shift) for employee_id in available_employee_ids])


    def validate_schedule(self, day):
        today_shifts = [self.get_shift(shift) for shift in range(self.num_shifts) if self.schedule[day][shift] != []]
        if not Scheduler.are_shifts_continuous_within_range(today_shifts, 8, 22):
            print(f"Day {self.day_labels[day]} is not continuous")
        NUM_ASSIGNEES_REQUIRED = 2
        current_num_assignees = self.get_num_assignees_within_range(day, 18, 22)
        while NUM_ASSIGNEES_REQUIRED - current_num_assignees > 0:
            # print(f"Day {self.day_labels[day]} has only one assignee from 18-22")
            assigned = self.assign_employee_to_shift(day, 4)
            if not assigned:
                print(f"Day {self.day_labels[day]} has only one assignee from 18-22")
                break
            current_num_assignees += 1

    
    def assign_employee_to_shift(self, day, shift):
        available_employee_ids = self.get_available_employee_ids_for_shift(day, shift)
        prioritized_employees = self.prioritize_employees(available_employee_ids, day, shift)
        while not prioritized_employees.is_empty() and self.schedule[day][shift] == []:
            employee = prioritized_employees.pop().employee
            if self.can_assign(employee, day, shift):
                self.schedule[day][shift].append(employee.id)
                employee.set_workload(employee.workload + self.get_shift(shift).get_workload_value())
        
        # if no one is available for the shift, assign backup shift
        if self.schedule[day][shift] == []:
            backup_shift = self.get_shift(shift).backup_shift
            if backup_shift is not None:
                self.assign_employee_to_shift(day, backup_shift)
        return self.schedule[day][shift] != []


    def assign_work(self):
        for day in range(self.num_days):
            shifts = self.prioritize_shifts(day)
            for shift in shifts:
                self.assign_employee_to_shift(day, shift)
            self.validate_schedule(day)
        return self.schedule
    

    def print_schedule(self):
        header = "\t"
        for day in  self.day_labels:
            header += f"{day}\t"
        print(header)
        for shift in range(self.num_shifts):
            row = f"{self.shift_labels[shift]}\t"
            for day in range(self.num_days):
                if self.schedule[day][shift] == []:
                    row += f"None\t"
                else:
                    employees = self.schedule[day][shift]
                    employee_names = ", ".join([self.get_employee(employee).name for employee in employees])
                    row += f"{employee_names}\t"
            print(row)
        
        print("\nWorkload:")
        for employee in self.employees:
            print(f"{employee.name}: {employee.workload}")

def read_input():
    shift_labels = ["08->12", "12->16", "14->18", "16->22", "18->22"]
    # read input from csv file
    with open('data.csv', newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=';')
        employee_names = []
        availability = []
        next(reader)  # Skip the header row
        for row in reader:
            employee_names.append(row[0]) # first cell in row is employee name
            availability.append([]) # list of availability for each day of the employee
            for cell_index, cell in enumerate(row[1:]):
                if cell.lower() == 'off':
                    availability[-1].append([])
                elif cell.lower() == 'free':
                    availability[-1].append([i for i in range(len(shift_labels))])
                else:
                    avail = [shift_labels.index(shift.strip()) for shift in cell.split(",")]
                    availability[-1].append(avail)
    return availability, employee_names
            

def main():
    day_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    shift_labels = ["8-12", "12-16", "14-18", "16-22", "18-22"]

    availability, employee_names = read_input()
    # print(availability)
    # # print(employee_names)
    # print ("Availability")
    # for i in range(len(employee_names)):
    #     print(f"{employee_names[i]}: {availability[i]}")
    scheduler = Scheduler(availability, employee_names, day_labels, shift_labels, 20)
    schedule = scheduler.assign_work()
    # print(schedule)
    scheduler.print_schedule()
    # for shift in scheduler.shifts:
    #     print(shift.label)
    # print(Scheduler.are_shifts_continuous_within_range([scheduler.get_shift(0), scheduler.get_shift(1), scheduler.get_shift(2)]))



if __name__ == "__main__":
    main()