function show_requirement_editing(id) {
    document.getElementById('view-'+id).style.display = 'none';
    document.getElementById('edit-'+id).style.display = '';
}

function hide_requirement_editing(id) {
    document.getElementById('view-'+id).style.display = '';
    document.getElementById('edit-'+id).style.display = 'none';
}

function toggle_requirement_details(id) {
    if (document.getElementById('details-'+id).style.display == '') {
        document.getElementById('details-'+id).style.display = 'none';
    } else {
        document.getElementById('details-'+id).style.display = '';
    }
}

function copy_id(req_set_id, req_id) {
    navigator.clipboard.writeText(req_set_id + ':' + req_id);
}

function link_to(to_req_set_id, to_req_id) {
    prepare_link_dialog(to_req_set_id, to_req_id, 'to');
}

function link_from(from_req_set_id, from_req_id) {
    prepare_link_dialog(from_req_set_id, from_req_id, 'from');
}

function prepare_link_dialog(req_set_id, req_id, direction) {
    let direction_statement = '';
    if (direction == 'from') {
        direction_statement = 'Linking from this requirement:';
    } else if (direction == 'to') {
        direction_statement = 'Linking to requirement:';
    }

    document.getElementById('linking_direction_statement').innerHTML = direction_statement;
    document.getElementById('requirement_html').innerHTML = document.getElementById('view-'+req_id).innerHTML;

    document.querySelectorAll('.this_requirement_value').forEach(e => {
        e.value = req_id;
    });

    document.querySelectorAll('.link_direction').forEach(e => {
        e.value = direction;
    });
}

function change_linked_requirement_set() {
    selected_set_id = document.querySelector('#selected_linked_requirement_set').value;

    document.querySelectorAll('.linked_requirement_set').forEach(e => {
        e.style.display = 'none';
    });

    document.querySelectorAll('.requirement_set_'+selected_set_id).forEach(e => {
        e.style.display = '';
    });
}

function move_requirement(req_set_id, req_id, new_position) {
    const body = {
        'index': new_position
    }

    request = {
        'method': 'POST',
        'body': JSON.stringify(body),
        'headers': {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    };

    fetch('/requirement_set/'+req_set_id+'/' + req_id + '/move', request).then((response) => {
        if (response.status != 200) {
            alert("Something went wrong!");
        }
    });

}

