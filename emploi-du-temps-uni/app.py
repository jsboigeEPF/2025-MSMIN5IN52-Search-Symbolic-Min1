#!/usr/bin/env python3
"""
Application Flask pour l'interface web de planification d'emploi du temps universitaire.
"""

from flask import Flask, render_template, request, jsonify
import minizinc
import json
import os
import logging
import traceback

app = Flask(__name__)

# basic logging to file for easier debugging
log_path = os.path.join(os.path.dirname(__file__), 'app.log')
logging.basicConfig(filename=log_path, level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s')
logger = logging.getLogger(__name__)

def solve_timetable():
    """Résoudre le problème d'emploi du temps avec MiniZinc."""
    try:
        model = minizinc.Model("timetable.mzn")
        # generate temporary data.dzn from teachers/courses
        temp_path, slot_datetimes, num_rooms, num_teachers, num_events, event_infos, room_capacity = generate_temp_dzn()
        if num_teachers == 0:
            return {'status': 'error', 'message': 'Aucun professeur défini. Créez au moins un professeur.'}
        if num_events == 0:
            return {'status': 'error', 'message': 'Aucun cours défini. Créez au moins un cours.'}
        model.add_file(temp_path)
        solver = minizinc.Solver.lookup("gecode")
        instance = minizinc.Instance(solver, model)
        result = instance.solve()

        # temp dzn provided event arrays; we'll map results to datetimes using slot_datetimes

        # Accept any of the satisfied/optimal statuses that the installed MiniZinc
        # Python binding provides (names vary between versions).
        ok_statuses = {minizinc.Status.SATISFIED}
        if hasattr(minizinc.Status, "OPTIMAL_SOLUTION"):
            ok_statuses.add(minizinc.Status.OPTIMAL_SOLUTION)
        if hasattr(minizinc.Status, "SATISFIED_OPTIMAL"):
            ok_statuses.add(minizinc.Status.SATISFIED_OPTIMAL)
        if result.status in ok_statuses:
            # Préparer les données pour le calendrier — extraire proprement les tableaux retournés
            events = []
            try:
                # result[...] may be a MiniZinc array-like; convert to plain Python lists
                event_start_raw = result['event_start']
                event_room_raw = result['event_room']
            except Exception:
                return {'status': 'error', 'message': 'Résultat MiniZinc inattendu (variables manquantes).'}

            # Convert to integer lists (MiniZinc arrays are 1-based); iteration will preserve order
            try:
                event_starts = [int(x) for x in event_start_raw]
            except Exception:
                # fallback: try to iterate keys in case of 1-based mapping
                try:
                    event_starts = [int(event_start_raw[i]) for i in sorted(event_start_raw.keys())]
                except Exception:
                    return {'status': 'error', 'message': 'Impossible de lire event_start depuis le résultat MiniZinc.'}

            try:
                event_rooms = [int(x) for x in event_room_raw]
            except Exception:
                try:
                    event_rooms = [int(event_room_raw[i]) for i in sorted(event_room_raw.keys())]
                except Exception:
                    return {'status': 'error', 'message': 'Impossible de lire event_room depuis le résultat MiniZinc.'}

            # optional durations
            event_durations = None
            # Avoid using `in` on `result` (minizinc.Result may treat keys as ints internally).
            # Safely try to retrieve `event_duration` and convert to list if present.
            try:
                raw_dur = result['event_duration']
            except Exception:
                raw_dur = None
            if raw_dur is not None:
                try:
                    event_durations = [int(x) for x in raw_dur]
                except Exception:
                    try:
                        # handle mapping-like result with integer keys
                        event_durations = [int(raw_dur[i]) for i in sorted(raw_dur.keys())]
                    except Exception:
                        event_durations = None

            # Build event objects
            # assign colors per course
            palette = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b','#e377c2','#7f7f7f','#bcbd22','#17becf']
            course_color = {}
            for info in event_infos:
                cid = info.get('course_id')
                if cid not in course_color:
                    course_color[cid] = palette[len(course_color) % len(palette)]

            for idx, start_slot in enumerate(event_starts):
                slot_index = int(start_slot) - 1
                if 0 <= slot_index < len(slot_datetimes):
                    dt = slot_datetimes[slot_index]
                    start_time = dt.isoformat()
                    # determine duration: prefer solver-provided durations, otherwise use event_infos
                    dur = 1
                    if event_durations and idx < len(event_durations):
                        dur = max(1, int(event_durations[idx]))
                    else:
                        try:
                            if idx < len(event_infos):
                                dur = max(1, int(event_infos[idx].get('duration', 1)))
                        except Exception:
                            dur = 1
                    end_time = (dt + __import__('datetime').timedelta(hours=dur)).isoformat()
                else:
                    start_time = None
                    end_time = None

                room = event_rooms[idx] if idx < len(event_rooms) else 1
                info = event_infos[idx] if idx < len(event_infos) else {}
                title = f"{info.get('course_name','Cours')} — {info.get('teacher_name','')}"
                color = course_color.get(info.get('course_id'), None)
                events.append({
                    'title': title,
                    'start': start_time,
                    'end': end_time,
                    'room_id': int(room),
                    'room_name': f'Salle {int(room)}',
                    'course_id': info.get('course_id'),
                    'color': color
                })

            return {'status': 'success', 'events': events, 'num_rooms': num_rooms, 'room_capacity': room_capacity}
        elif result.status == minizinc.Status.UNSATISFIABLE:
            return {'status': 'error', 'message': 'Le problème est insatisfiable.'}
        else:
            return {'status': 'error', 'message': f'Statut inconnu: {result.status}'}
    except Exception as e:
        # collect detailed debug info
        tb = traceback.format_exc()
        info = {
            'type': type(e).__name__,
            'message': str(e),
            'traceback': tb
        }
        # try to include the MiniZinc result representation if available
        try:
            info['result_repr'] = repr(result)
            info['result_type'] = str(type(result))
        except Exception:
            pass
        # include some local variables if present
        for key in ('temp_path', 'slot_datetimes', 'num_rooms', 'num_teachers', 'num_events'):
            try:
                info[key] = locals().get(key)
            except Exception:
                info[key] = None

        try:
            logger.error('solve_timetable error: %s', json.dumps(info, default=str))
        except Exception:
            logger.error('solve_timetable error (logging failed): %s', str(e))

        # return a concise message plus a short traceback snippet for debugging in the UI
        tb_snippet = tb.splitlines()[-10:]
        return {
            'status': 'error',
            'message': f"{type(e).__name__}: {str(e)}",
            'details': '\n'.join(tb_snippet),
            'log_file': os.path.relpath(log_path, os.path.dirname(__file__))
        }


def _teachers_file_path():
    return os.path.join(os.path.dirname(__file__), 'teachers.json')


def _courses_file_path():
    return os.path.join(os.path.dirname(__file__), 'courses.json')


def load_courses():
    path = _courses_file_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def save_courses(courses):
    path = _courses_file_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)


@app.route('/courses', methods=['GET'])
def get_courses():
    return jsonify({'status': 'success', 'courses': load_courses()})


@app.route('/courses', methods=['POST'])
def create_course():
    try:
        data = request.get_json()
        # expected fields: name, teacher_id, students, duration, total_sessions
        for key in ('name', 'teacher_id', 'students', 'duration', 'total_sessions'):
            if key not in data:
                return jsonify({'status': 'error', 'message': f'Missing {key}'}), 400
        courses = load_courses()
        new_id = 1
        if courses:
            new_id = max(c.get('id', 0) for c in courses) + 1
        course = {
            'id': new_id,
            'name': data['name'],
            'teacher_id': int(data['teacher_id']),
            'students': int(data['students']),
            'duration': int(data['duration']),
            'total_sessions': int(data['total_sessions'])
        }
        courses.append(course)
        save_courses(courses)
        return jsonify({'status': 'success', 'course': course})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/courses/<int:course_id>', methods=['DELETE'])
def delete_course(course_id):
    try:
        courses = load_courses()
        new_courses = [c for c in courses if int(c.get('id', -1)) != int(course_id)]
        if len(new_courses) == len(courses):
            return jsonify({'status': 'error', 'message': 'Cours introuvable.'}), 404
        save_courses(new_courses)
        return jsonify({'status': 'success', 'message': 'Cours supprimé.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


def generate_temp_dzn():
    """Generate a temporary .dzn from current teachers and courses and return (path, slot_datetimes, num_rooms).
    Slots cover Sept 1 to Nov 30 of the current year, weekdays Mon-Fri, 8 slots per day.
    Hours: 09:00,10:00,11:00,13:00,14:00,15:00,16:00,17:00 (no classes during 12:00-13:00, classes may end at 18:00).
    """
    from datetime import date, datetime, timedelta, time

    base_dir = os.path.dirname(__file__)
    # read room capacities from data.dzn
    data_path = os.path.join(base_dir, 'data.dzn')
    num_rooms = 10
    room_capacity = []
    if os.path.exists(data_path):
        txt = open(data_path, 'r', encoding='utf-8').read()
        import re
        m = re.search(r"num_rooms\s*=\s*(\d+)", txt)
        if m:
            num_rooms = int(m.group(1))
        m2 = re.search(r"room_capacity\s*=\s*\[(.*?)\]", txt, re.S)
        if m2:
            arr = [int(x.strip()) for x in m2.group(1).split(',') if x.strip()]
            room_capacity = arr
    if not room_capacity:
        room_capacity = [40] * num_rooms

    teachers = load_teachers()
    courses = load_courses()

    # date range
    year = datetime.now().year
    start_date = date(year, 9, 1)
    end_date = date(year, 11, 30)

    # generate slot datetimes list
    slot_datetimes = []
    # define allowed start hours per day (exclude 12:00-13:00); last start at 17:00 so classes end by 18:00
    allowed_hours = [9,10,11,13,14,15,16,17]
    for single in (start_date + timedelta(n) for n in range((end_date - start_date).days + 1)):
        if single.weekday() < 5:  # Mon-Fri
            for h in allowed_hours:
                slot_datetimes.append(datetime.combine(single, time(h,0)))

    num_slots = len(slot_datetimes)

    # build teacher_available: TEACHERS x SLOTS
    teacher_available = []
    # map day names used in UI to weekday index
    day_map = {'Mon':0,'Tue':1,'Wed':2,'Thu':3,'Fri':4,'Sat':5,'Sun':6}
    for t in teachers:
        avail = [0]*num_slots
        av = t.get('availability', {}) or {}
        # build quick lookup per weekday of ranges
        ranges_by_wd = {}
        for dn, arr in av.items():
            wd = day_map.get(dn)
            if wd is None: continue
            ranges_by_wd[wd] = []
            for pair in arr:
                try:
                    s = pair[0]
                    e = pair[1]
                    # parse hh:mm
                    sh, sm = map(int, s.split(':'))
                    eh, em = map(int, e.split(':'))
                    ranges_by_wd[wd].append((sh,eh))
                except Exception:
                    continue
        # fill avail
        for idx, dt in enumerate(slot_datetimes):
            wd = dt.weekday()
            hour = dt.hour
            ok = 0
            if wd in ranges_by_wd:
                for (sh,eh) in ranges_by_wd[wd]:
                    if hour >= sh and hour < eh:
                        ok = 1
                        break
            avail[idx] = ok
        teacher_available.extend(avail)

    # expand courses into events (sessions) and build event metadata
    event_teacher = []
    event_duration = []
    event_students = []
    event_infos = []  # metadata per expanded event, in same order
    event_course = []  # map each event to its course index (1..num_courses)
    # build teacher name map
    teacher_map = {t.get('id'): t.get('name') for t in teachers}
    # also build max_days_per_course (default to number of weekdays)
    num_courses = len(courses)
    max_days_per_course = []
    for ci, c in enumerate(courses, start=1):
        sessions = int(c.get('total_sessions', 1))
        duration = int(c.get('duration', 1))
        students = int(c.get('students', 10))
        teacher_id = int(c.get('teacher_id', 1))
        maxd = int(c.get('max_days_per_week', 6))
        max_days_per_course.append(maxd)
        for _ in range(sessions):
            event_teacher.append(teacher_id)
            event_duration.append(duration)
            event_students.append(students)
            event_course.append(ci)
            event_infos.append({
                'course_id': int(c.get('id', 0)),
                'course_name': c.get('name'),
                'teacher_id': teacher_id,
                'teacher_name': teacher_map.get(teacher_id, f'Professeur {teacher_id}'),
                'students': students,
                'duration': duration
            })

    num_events = len(event_teacher)

    # compute slot_weekday mapping (weekday index 1..num_weekdays) and slot_hour/day
    # We consider Monday..Saturday -> 1..6
    slot_weekday = [ (dt.weekday() + 1) for dt in slot_datetimes ]
    slot_hour = [ dt.hour for dt in slot_datetimes ]
    slot_day = [ (dt.date() - start_date).days + 1 for dt in slot_datetimes ]

    # write temp dzn
    temp_path = os.path.join(base_dir, 'temp_data.dzn')
    with open(temp_path, 'w', encoding='utf-8') as f:
        f.write(f"num_events = {num_events};\n")
        f.write(f"num_slots = {num_slots};\n")
        f.write(f"num_rooms = {num_rooms};\n")
        f.write(f"num_teachers = {len(teachers)};\n")
        f.write(f"num_courses = {num_courses};\n")
        f.write(f"num_weekdays = 6;\n")
        # arrays
        def write_array(name, arr):
            f.write(f"{name} = [")
            f.write(', '.join(str(x) for x in arr))
            f.write('];\n')

        write_array('event_teacher', event_teacher)
        write_array('event_duration', event_duration)
        write_array('event_students', event_students)
        write_array('event_course', event_course)
        # room_capacity
        write_array('room_capacity', room_capacity)
        # max_days_per_course
        write_array('max_days_per_course', max_days_per_course)
        # slot_weekday, slot_hour, slot_day
        write_array('slot_weekday', slot_weekday)
        write_array('slot_hour', slot_hour)
        write_array('slot_day', slot_day)
        # teacher_available as array2d(TEACHERS, SLOTS, [...])
        f.write('teacher_available = array2d(TEACHERS, SLOTS, [')
        f.write(', '.join(str(x) for x in teacher_available))
        f.write(']);\n')

    return temp_path, slot_datetimes, num_rooms, len(teachers), num_events, event_infos, room_capacity


def load_teachers():
    path = _teachers_file_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def save_teachers(teachers):
    path = _teachers_file_path()
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(teachers, f, ensure_ascii=False, indent=2)


@app.route('/teachers/<int:teacher_id>', methods=['DELETE'])
def delete_teacher(teacher_id):
    try:
        teachers = load_teachers()
        courses = load_courses()
        # if any course references this teacher, refuse deletion
        linked = [c for c in courses if int(c.get('teacher_id', -1)) == int(teacher_id)]
        if linked:
            return jsonify({'status': 'error', 'message': "Impossible de supprimer le professeur: il est affecté à au moins un cours."}), 400
        new_teachers = [t for t in teachers if int(t.get('id', -1)) != int(teacher_id)]
        if len(new_teachers) == len(teachers):
            return jsonify({'status': 'error', 'message': 'Professeur introuvable.'}), 404
        save_teachers(new_teachers)
        return jsonify({'status': 'success', 'message': 'Professeur supprimé.'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/teachers', methods=['GET'])
def get_teachers():
    return jsonify({'status': 'success', 'teachers': load_teachers()})


@app.route('/teachers', methods=['POST'])
def create_teacher():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'status': 'error', 'message': 'Missing name'}), 400
        teachers = load_teachers()
        new_id = 1
        if teachers:
            new_id = max(t.get('id', 0) for t in teachers) + 1
        teacher = {
            'id': new_id,
            'name': data.get('name'),
            'availability': data.get('availability', {})
        }
        teachers.append(teacher)
        save_teachers(teachers)
        return jsonify({'status': 'success', 'teacher': teacher})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/solve', methods=['POST'])
def solve():
    result = solve_timetable()
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)