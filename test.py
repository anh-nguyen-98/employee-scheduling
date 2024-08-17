import heapq
import math
import csv
import utils
import re

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
        self.backup_shift_id = -1

    def get_workload_value(self):
        # workload value can be adjusted here
        return 1
    
    def set_backup(self, shift_id):
        self.backup_shift_id = shift_id


class TimeRangeShift(Shift):
    def __init__(self, id, label) -> None:
        super().__init__(id, label)
        parts = list(map(int, re.findall(r'\d+', label)))
        self.start_time = parts[0]
        self.end_time = parts[1]
        self.workload_value = self.end_time - self.start_time
    
    def get_workload_value(self):
        return self.workload_value
        
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
    def __init__(self, availability, employee_names, day_labels, shift_labels, work_limit=None, total_workload_limit=120) -> None:
        self.day_labels = day_labels
        self.shift_labels = shift_labels
        self.num_employees = len(employee_names)
        self.num_days = len(day_labels)
        self.num_shifts = len(shift_labels)

        self.employees = [Employee(i, employee_names[i], i, availability[i]) for i in range(self.num_employees)]
        self.shifts = [TimeRangeShift(i, shift_labels[i]) for i in range(self.num_shifts)]
        self.shifts = sorted(self.shifts, key=lambda shift: shift.start_time)
        self.main_shift_ids = [shift.id for shift in self.shifts if shift.is_main_shift]

        self.shift_availability = self.create_shift_availability(availability)

        self.TOTAL_WORKLOAD_LIMIT = total_workload_limit
        self.total_workload = 0

        self.WORKLOAD_LIMIT_PER_PERSON = self.calculate_workload_limit() if work_limit is None else work_limit
        

        self.schedule = [[[] for _ in range(self.num_shifts)] for _ in range(self.num_days)] # schedule[day][shift] = [employee_id] list of employees assigned to that shift in that day

        self.assignment = [[-1 for _ in range(self.num_days)] for _ in range(self.num_employees)]

    def get_shift_id_by_label(self, shift_label):
        for shift in self.shifts:
            if shift.label == shift_label:
                return shift.id
        return -1

    def set_backup_shift(self, shift_label, backup_shift_label):
        shift_id = self.get_shift_id_by_label(shift_label)
        backup_shift_id = self.get_shift_id_by_label(backup_shift_label)
        self.get_shift(shift_id).set_backup(backup_shift_id)
        self.get_shift(backup_shift_id).is_main_shift = False
        self.main_shift_ids.remove(backup_shift_id)


    @staticmethod
    def are_shifts_continuous_within_time_range(shifts, start_time, end_time):
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

    def is_total_workload_exceeded(self, day_index, shift_index):
        shift_workload = self.get_shift(shift_index).get_workload_value()
        if self.total_workload >= self.TOTAL_WORKLOAD_LIMIT:
            return True
        if shift_workload + self.total_workload > self.TOTAL_WORKLOAD_LIMIT:
            return True
        return False


    def can_assign(self, employee: Employee, day, shift):
        # MORE CONDITIONS CAN BE ADDED HERE
        # shift_workload = self.get_shift(shift).get_workload_value()
        # if employee.workload >= self.WORKLOAD_LIMIT_PER_PERSON or employee.workload + shift_workload > self.WORKLOAD_LIMIT_PER_PERSON:
        #     return False
        for shift in self.schedule[day]:
            if employee.id in shift:
                return False
        return True
    
    def get_shifts_within_time_range(self, start_time, end_time):
        return [shift.id for shift in self.shifts if shift.start_time <= start_time and shift.end_time >= end_time]
    
    def get_available_employee_ids_for_shift(self, day_index, shift_index):
        shift_ids = self.get_shifts_within_time_range(self.get_shift(shift_index).start_time, self.get_shift(shift_index).end_time)
        available_employee_ids = set()
        for shift_id in shift_ids:
            available_employee_ids.update(self.shift_availability[day_index][shift_id])
        return list(available_employee_ids)

    def get_num_assignees_within_time_range(self, day_index, start_time, end_time):
        shift_ids = self.get_shifts_within_time_range(start_time, end_time)
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

    def prioritize_employees(self, available_employee_ids, day_index, shift_index) -> PriorityQueue:
        return PriorityQueue([EmployeeComparator(self.get_employee(employee_id), day_index, shift_index) for employee_id in available_employee_ids])


    def validate_schedule(self, day_index):
        today_shifts = [self.get_shift(shift_index) for shift_index in range(self.num_shifts) if self.schedule[day_index][shift_index] != []]
        if not Scheduler.are_shifts_continuous_within_time_range(today_shifts, 8, 22):
            print(f"Day {self.day_labels[day_index]} is not continuous")

        extra_requirement = {
            "start_time": 18,
            "end_time": 22,
            "num_assignees_required": 2,
            "shift_id_to_assign_extra": self.get_shift_id_by_label("18->22")
        }

        current_num_assignees = self.get_num_assignees_within_time_range(day_index, extra_requirement["start_time"], extra_requirement["end_time"])
        to_assign = extra_requirement["num_assignees_required"] - current_num_assignees
        assigned = self.assign_employees_to_shift(day_index, extra_requirement["shift_id_to_assign_extra"], to_assign)
        if assigned < to_assign:
            current_num_assignees = self.get_num_assignees_within_time_range(day_index, extra_requirement["start_time"], extra_requirement["end_time"])
            print(f"Day {self.day_labels[day_index]} have only {current_num_assignees} assignees for shift 18->22, but {extra_requirement["num_assignees_required"]} required")

        
    def validate_schedule_final(self):
        for employee in self.employees:
            day = 0
            while employee.workload < self.WORKLOAD_LIMIT_PER_PERSON and day < self.num_days:
                # check if employee is available for any shift
                for shift in employee.availability_in_week[day]:
                    if self.can_assign(employee, day, shift):
                        self.schedule[day][shift].append(employee.id)
                        employee.set_workload(employee.workload + self.get_shift(shift).get_workload_value())
                        break
                day += 1

    
    def assign_employees_to_shift(self, day_index, shift_index, to_assign=1):
        shift_workload = self.get_shift(shift_index).get_workload_value()
        available_employee_ids = self.get_available_employee_ids_for_shift(day_index, shift_index)
        prioritized_employees = self.prioritize_employees(available_employee_ids, day_index, shift_index)
        assigned = 0
        while not prioritized_employees.is_empty() and assigned < to_assign:
            employee = prioritized_employees.pop().employee
            if self.can_assign(employee, day_index, shift_index):
                self.schedule[day_index][shift_index].append(employee.id)
                self.assignment[employee.id][day_index] = shift_index
                employee.set_workload(employee.workload + shift_workload)
                self.total_workload += shift_workload
                assigned += 1
        
        # if no one is available for the shift, assign backup shift
        if assigned < to_assign:
            backup_shift_id = self.get_shift(shift_index).backup_shift_id
            if backup_shift_id != -1:
                self.assign_employees_to_shift(day_index, backup_shift_id, to_assign)
        return assigned


    def assign_work(self):
        for day_index in range(self.num_days):
            shift_ids = self.prioritize_shifts(day_index)
            for shift_index in shift_ids:
                if self.is_total_workload_exceeded(day_index, shift_index):
                    print(f"Total workload exceeded. Current workload: {self.total_workload}. Limit: {self.TOTAL_WORKLOAD_LIMIT}")
                    unassigned_shifts = shift_ids[shift_ids.index(shift_index):]
                    print(f"Unassigned shifts on day {self.day_labels[day_index]}: {[self.shift_labels[shift_id] for shift_id in unassigned_shifts]}. And other days after this day")
                    return self.schedule
                self.assign_employees_to_shift(day_index, shift_index)
            self.validate_schedule(day_index)
        self.validate_schedule_final()
        return self.schedule
    

    def print_schedule(self):
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
                        employees = self.schedule[day][shift]
                        employee_names = ", ".join([self.get_employee(employee).name for employee in employees])
                        row.append(employee_names)
                writer.writerow(row)
        print ("Schedule is written to schedule.csv")

        # write assignment of each employee to csv file
        with open('assignment.csv', mode='w', newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter=';')
            writer.writerow(["Employee"] + self.day_labels + ["Total Workload"])
            for employee in self.employees:
                row = [employee.name]
                for day in range(self.num_days):
                    shift = self.assignment[employee.id][day]
                    if shift == -1:
                        row.append("None")
                    else:
                        row.append(self.shift_labels[shift])
                row.append(employee.workload)
                writer.writerow(row)
        print ("Assignment is written to assignment.csv")
            

def main():
    shift_labels = ["08->12", "12->16", "14->18", "16->22", "18->22"]

    day_labels, employee_names, availability = utils.read_input(shift_labels)
    scheduler = Scheduler(availability, employee_names, day_labels, shift_labels, 25)
    scheduler.set_backup_shift("16->22", "14->18") # 14-18 is backup for 16-22
    schedule = scheduler.assign_work()
    # # print(schedule)
    scheduler.print_schedule()

if __name__ == "__main__":
    main()