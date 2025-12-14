% University Timetabling Model in MiniZinc
% This model assigns time slots and rooms to courses/exams
% Constraints: no overlaps for teachers/rooms, capacity, etc.

include "globals.mzn";

% Parameters (to be defined in data file)
int: num_events;  % Number of courses/exams
int: num_slots;   % Number of time slots (e.g., 5 days * 8 hours = 40)
int: num_rooms;   % Number of rooms
int: num_teachers; % Number of teachers
int: num_courses;  % Number of distinct courses (groups of events)
int: num_weekdays; % Number of weekdays considered (e.g., 6 for Mon..Sat)

set of int: EVENTS = 1..num_events;
set of int: SLOTS = 1..num_slots;
set of int: ROOMS = 1..num_rooms;
set of int: TEACHERS = 1..num_teachers;
set of int: COURSES = 1..num_courses;
set of int: WEEKDAYS = 1..num_weekdays;

% Event data
array[EVENTS] of int: event_teacher;  % Teacher assigned to each event
array[EVENTS] of int: event_duration; % Duration in slots (assume 1 for simplicity)
array[EVENTS] of int: event_students; % Number of students
array[EVENTS] of int: event_course;   % course id for each event (1..num_courses)

% Room data
array[ROOMS] of int: room_capacity;   % Capacity of each room

% Teacher availability (1 if available, 0 if not)
array[TEACHERS, SLOTS] of 0..1: teacher_available;
array[SLOTS] of WEEKDAYS: slot_weekday; % weekday index (1..num_weekdays) for each slot
array[SLOTS] of int: slot_hour; % hour of day for each slot (e.g., 9,10,11,13,...)
array[SLOTS] of int: slot_day;  % day index (monotonic day id) for each slot

% Variables
array[EVENTS] of var SLOTS: event_start;  % Start time slot for each event
array[EVENTS] of var ROOMS: event_room;   % Room assigned to each event
array[EVENTS] of var WEEKDAYS: event_wday; % computed weekday for each event start

% ensure events fit within available slots
constraint forall(e in EVENTS)(
    event_start[e] + event_duration[e] - 1 <= num_slots
);

% Constraints

% 1. No two events in the same room at overlapping times
constraint forall(i,j in EVENTS where i < j)(
    event_room[i] != event_room[j] 
    \/ event_start[i] + event_duration[i] - 1 < event_start[j]
    \/ event_start[j] + event_duration[j] - 1 < event_start[i]
);

% 2. Teacher conflicts: no two events for same teacher with overlapping times
constraint forall(i,j in EVENTS where i < j /\
                      event_teacher[i] == event_teacher[j])(
    event_start[i] + event_duration[i] - 1 < event_start[j]
    \/ event_start[j] + event_duration[j] - 1 < event_start[i]
);

% 3. Room capacity
constraint forall(e in EVENTS)(
    event_students[e] <= room_capacity[event_room[e]]
);

% 4. Teacher availability across the whole duration
constraint forall(e in EVENTS)(
    forall(k in 0..event_duration[e]-1)(
        teacher_available[event_teacher[e], event_start[e] + k] == 1
    )
);

% Link event weekday to slot_weekday via element constraint
constraint forall(e in EVENTS)(
    event_wday[e] = slot_weekday[event_start[e]]
);

% Ensure multi-hour events occupy contiguous real hours (no crossing lunch gaps)
constraint forall(e in EVENTS)(
    forall(k in 0..event_duration[e]-1)(
        slot_hour[event_start[e] + k] = slot_hour[event_start[e]] + k
    )
);

% Also ensure events stay within the same calendar day (do not cross midnight or next day)
constraint forall(e in EVENTS)(
    forall(k in 0..event_duration[e]-1)(
        slot_day[event_start[e] + k] = slot_day[event_start[e]]
    )
);

% COURSE weekday-usage constraint:
% For each course c and weekday w, used[c,w] = 1 if course has any event on weekday w.
array[COURSES, WEEKDAYS] of var 0..1: used;
array[COURSES] of int: max_days_per_course; % maximum distinct weekdays allowed per course

constraint forall(c in COURSES, w in WEEKDAYS)(
    used[c,w] = bool2int(exists(e in EVENTS where event_course[e] == c)(event_wday[e] == w))
);

% enforce course-level limit
constraint forall(c in COURSES)(
    sum(w in WEEKDAYS)(used[c,w]) <= max_days_per_course[c]
);

% 5. Optional: No event starts at invalid slots, but assume all slots are valid

% Objective: For now, just satisfy (find any feasible assignment)
% Later, can add minimize total conflicts or something

% Prefer assigning events to small rooms that still fit the student count.
% Minimize the total capacity used across all events (heuristic).
solve minimize sum(e in EVENTS)(room_capacity[event_room[e]]);

% Output
output [
    "Emploi du temps universitaire:\n" ++
    concat([ "Cours " ++ show(e) ++ ": Enseignant " ++ show(event_teacher[e]) ++
             ", Début " ++ show(event_start[e]) ++ ", Salle " ++ show(event_room[e]) ++ "\n"
             | e in EVENTS ])
];