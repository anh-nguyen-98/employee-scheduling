import heapq
import math


class Employee:
    def __init__(self, id, name, availability) -> None:
        self.id = id
        self.name = name
        self.availability = availability
        self.workload = 0

    # compare employees
    def __lt__(self, other):
        # TODO: more criteria to prioritize employees when assigning work can be added here
        if self.workload == other.workload:
            return len(self.availability) < len(other.availability)
        return self.workload < other.workload
    
    def set_workload(self, workload):
        self.workload = workload


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
    def __init__(self, availability, employee_names, day_labels, shift_labels) -> None:
        self.day_labels = day_labels
        self.shift_labels = shift_labels
        self.num_employees = len(employee_names)
        self.num_days = len(day_labels)
        self.num_shifts = len(shift_labels)

        self.employees = [Employee(i, employee_names[i], availability[i]) for i in range(self.num_employees)]

        self.shift_availability = self.create_shift_availability(availability)

        self.WORKLOAD_LIMIT_PER_PERSON = self.calculate_workload_limit()

        self.schedule = [[-1 for _ in range(self.num_shifts)] for _ in range(self.num_days)]


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
                    shift_availability[day][shift].append(self.employees[person_id])
        return shift_availability


    def can_assign(self, employee, day, shift):
        # MORE CONDITIONS CAN BE ADDED HERE
        return employee.id not in self.schedule[day] and employee.workload < self.WORKLOAD_LIMIT_PER_PERSON


    def prioritize_shifts(self, day):
        # sort shifts by  number of available people in that day
        shifts = sorted(range(self.num_shifts), key=lambda shift: len(self.shift_availability[day][shift]))
        return shifts


    def assign_work(self):
        for day in range(self.num_days):
            shifts = self.prioritize_shifts(day)
            for shift in shifts:
                prioritized_people = PriorityQueue(self.shift_availability[day][shift])
                while not prioritized_people.is_empty() and self.schedule[day][shift] == -1: # -1 means no one is assigned yet
                    employee = prioritized_people.pop()
                    if self.can_assign(employee, day, shift):
                        self.schedule[day][shift] = employee.id
                        employee.set_workload(employee.workload + 1)

        return self.schedule
    

    def print_schedule(self):
        header = "\t"
        for day in  self.day_labels:
            header += f"{day}\t"
        print(header)
        for shift in range(self.num_shifts):
            row = f"{self.shift_labels[shift]}\t"
            for day in range(self.num_days):
                if self.schedule[day][shift] == -1:
                    row += f"None\t"
                else:
                    employee = self.employees[self.schedule[day][shift]]
                    row += f"{employee.name}\t"
            print(row)


def main():
    day_labels = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
    shift_labels = ["S", "T", "C"]
    employee_names = ["Dat", "Danh", "Khoi", "Anh", "Tan", "Tien"]
    availability = [
        [[0, 1], [0, 1], [], [1, 2], [0, 1, 2], [0, 2], [1, 2]],
        [[0, 2], [], [0, 1, 2], [0, 1], [1, 2], [0, 1], [0, 2]],
        [[0, 1], [0, 1], [1, 2], [], [0, 1], [0, 1, 2], [1, 2]],
        [[0, 1], [0, 1, 2], [1, 2], [1, 2], [], [0, 1], [1, 2]],
        [[0], [1, 2], [0, 1], [], [0, 1], [0, 1, 2], [1]],
        [[2], [2], [1], [0, 1], [2], [0], []]
    ]

    scheduler = Scheduler(availability, employee_names, day_labels, shift_labels)
    scheduler.assign_work()
    scheduler.print_schedule()


if __name__ == "__main__":
    main()