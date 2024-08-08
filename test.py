import heapq
import math

class Employee:
    def __init__(self, id, name, availability) -> None:
        self.id = id
        self.name = name
        self.availability = availability
        self.shifts_assigned = 0

    # compare employees
    def __lt__(self, other):
        if self.shifts_assigned == other.shifts_assigned:
            return len(self.availability) < len(other.availability)
        return self.shifts_assigned < other.shifts_assigned
    
    def set_shifts_assigned(self, shifts_assigned):
        self.shifts_assigned = shifts_assigned

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
    def __init__(self, availability, staff, shift_labels) -> None:
        self.num_people = len(staff)
        self.num_days = 7
        self.num_shifts = len(shift_labels)
        self.DAY_LABELS = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        self.SHIFT_LABELS = shift_labels
        
        self.employees = [Employee(i, staff[i], availability[i]) for i in range(self.num_people)]

        self.shift_availability = self.create_shift_availability(availability)

        self.schedule = [[-1 for _ in range(self.num_shifts)] for _ in range(self.num_days)]

        self.SHIFT_LIMIT_PER_PERSON  = math.ceil(self.num_days * self.num_shifts / self.num_people)
    
    def get_employee_by_id(self, id):
        return self.employees[id]
    
    def create_shift_availability(self, availability):
        # shift_availability[day][shift] = list of people available for that shift in that day
        shift_availability = [[[] for _ in range(self.num_shifts)] for _ in range(self.num_days)]
        for person_id, person_availability in enumerate(availability):
            # list of shifts that person is available for each day
            for day in range(self.num_days):
                for shift in person_availability[day]:
                    shift_availability[day][shift].append(self.get_employee_by_id(person_id))
        return shift_availability

    def valid(self, employee, day, shift):
        return employee.id not in self.schedule[day] and employee.shifts_assigned < self.SHIFT_LIMIT_PER_PERSON


    def prioritize_shifts(self, day):
        # sort shifts by  number of available people in that day
        shifts = sorted(range(self.num_shifts), key=lambda shift: len(self.shift_availability[day][shift]))
        return shifts


    def assign_shifts(self):
        for day in range(self.num_days):
            shifts = self.prioritize_shifts(day)
            for shift in shifts:
                prioritized_people = PriorityQueue(self.shift_availability[day][shift])
                while not prioritized_people.is_empty() and self.schedule[day][shift] == -1:
                    employee = prioritized_people.pop()
                    if self.valid(employee, day, shift):
                        self.schedule[day][shift] = employee.id
                        employee.set_shifts_assigned(employee.shifts_assigned + 1)

        return self.schedule
    
    def day_to_string(self, day):
        return self.DAY_LABELS[day]
    
    def shift_to_string(self, shift):
        return self.SHIFT_LABELS[shift]
    
    def print_schedule(self):
        header = "\t"
        for day in self.DAY_LABELS:
            header += f"{day}\t"
        print(header)
        for shift in range(self.num_shifts):
            row = f"{self.SHIFT_LABELS[shift]}\t"
            for day in range(self.num_days):
                if self.schedule[day][shift] == -1:
                    row += f"None\t"
                else:
                    employee = self.get_employee_by_id(self.schedule[day][shift])
                    row += f"{employee.name}\t"
            print(row)


def main():
    shift_labels = ["S", "T", "C"]
    employees = ["Dat", "Danh", "Khoi", "Anh", "Tan", "Tien"]
    availability = [
        [[0, 1], [0, 1], [], [1, 2], [0, 1, 2], [0, 2], [1, 2]],
        [[0, 2], [], [0, 1, 2], [0, 1], [1, 2], [0, 1], [0, 2]],
        [[0, 1], [0, 1], [1, 2], [], [0, 1], [0, 1, 2], [1, 2]],
        [[0, 1], [0, 1, 2], [1, 2], [1, 2], [], [0, 1], [1, 2]],
        [[0], [1, 2], [0, 1], [], [0, 1], [0, 1, 2], [1]],
        [[2], [2], [1], [0, 1], [2], [0], []]
    ]

    scheduler = Scheduler(availability, employees, shift_labels)
    scheduler.assign_shifts()
    scheduler.print_schedule()

if __name__ == "__main__":
    main()

