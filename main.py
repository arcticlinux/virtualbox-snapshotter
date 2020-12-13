import sys
from datetime import datetime

import virtualbox

vbox = virtualbox.VirtualBox()
session = virtualbox.Session()


def check_arguments():
    """


    :rtype : str
    """
    if len(sys.argv) < 2:
        print("Not enough argument provided")
        return 1
    elif not isinstance(sys.argv[1], str):
        print("Provided name is not a string")
        return 1
    return sys.argv[1]


def get_snapshots(snapshot, snapshots=None):
    """



    :type snapshot: IMachine
    :type snapshots: list|None
    :rtype : list
    """
    if snapshots is None:
        snapshots = []
        # Create an empty list when one doesn't exist
        # Don't add the root snapshot to the list
    else:
        # Add the current child snapshot id to the list
        snapshots.append(snapshot.id_p)
    if hasattr(snapshot, 'children'):
        for child in snapshot.children:
            get_snapshots(child, snapshots)
    return snapshots


def snapshot_info(machine, snapshot_id):
    """


    :type machine: IMachine
    :type snapshot_id: str
    :rtype : list
    """
    snapshot_obj = machine.find_snapshot(snapshot_id)
    date = datetime.fromtimestamp(snapshot_obj.time_stamp / 1000.0).strftime("%d-%m-%Y %H:%M:%S")
    return [snapshot_obj.name, date]


def delete_snapshots(machine, num_snapshots_to_keep=4):
    """


    :type machine: IMachine
    :type num_snapshots_to_keep: int
    :rtype : None
    """

    root_snapshot = machine.find_snapshot('')
    snapshots = get_snapshots(root_snapshot)

    if len(snapshots) > num_snapshots_to_keep:
        highest_snapshot_to_delete = len(snapshots) - num_snapshots_to_keep
        snapshots_to_delete = snapshots[:highest_snapshot_to_delete]
        if snapshots_to_delete:
            try:
                print()
                print('Deleting', len(snapshots_to_delete), 'snapshot(s):')
                machine.lock_machine(session, virtualbox.library.LockType(1))
                for snapshot in snapshots_to_delete:
                    print('- ', snapshot_to_string(machine, snapshot), snapshot)
                    process = session.machine.delete_snapshot(snapshot)
                    process.wait_for_completion(timeout=-1)
            except:
                print('Delete', machine.name, "snapshots failed")
                return


def create_snapshot(machine):
    """


    :type machine: IMachine
    :rtype : int
    """
    vm_initial_status = 1  # zero means powered on

    if machine.state == virtualbox.library.MachineState(1):  # MachineState(1) = PowerOff
        vm_initial_status = 0
        if session.state == virtualbox.library.SessionState(2):
            session.unlock_machine()
        proc = machine.launch_vm_process(session, "headless")
        proc.wait_for_completion(timeout=-1)

    snap_date = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    snap_name = 'Snapshot ' + snap_date
    # If there are no existing snapshots create a first snapshot with the machine name
    if machine.snapshot_count == 0:
        snap_name = machine.name
    description = 'Created at ' + snap_date

    if vm_initial_status:
        if machine.session_state == virtualbox.library.SessionState(2):  # SessionState(2) = Locked
            # The first IF check whether the machine is in locked session, the second one checks if
            # the session is locked
            if session.state == virtualbox.library.SessionState(2):
                session.unlock_machine()
        shared_lock_type = virtualbox.library.LockType(1)
        machine.lock_machine(session, shared_lock_type)

    process, unused_variable = session.machine.take_snapshot(snap_name, description, False)
    process.wait_for_completion(timeout=-1)
    print('Created: ' + description)

    if vm_initial_status:
        if session.state == virtualbox.library.SessionState(2):
            session.unlock_machine()

    return vm_initial_status


def snapshot_to_string(machine, snapshot):
    """


    :type machine: IMachine
    :type snapshot: str
    :rtype : str
    """
    return ', '.join([str(elem) for elem in snapshot_info(machine, snapshot)])


def print_snapshots_info(machine):
    """


    :rtype : None
    :type machine: IMachine
    """
    root_snapshot = machine.find_snapshot('')
    if machine.snapshot_count > 1:
        snapshots = get_snapshots(root_snapshot)
        print()
        print(machine.name, 'snapshots:')
        for snapshot in snapshots:
            print(snapshot_to_string(machine, snapshot))


def main():
    print('Starting auto snapshotter script ...')
    name = check_arguments()

    machine = vbox.find_machine(name)
    vm_status = create_snapshot(machine)
    if not vm_status:
        session.console.power_down()
    delete_snapshots(machine)
    print_snapshots_info(machine)


if __name__ == '__main__':
    main()
