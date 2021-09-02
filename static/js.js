function show_requirement_editing(id) {
    document.getElementById('view-'+id).style.display = 'none';
    document.getElementById('edit-'+id).style.display = 'inline-block';
}

function hide_requirement_editing(id) {
    document.getElementById('view-'+id).style.display = 'inline-block';
    document.getElementById('edit-'+id).style.display = 'none';
}

function save_requirement(req_set_id, req_id) {
    const original_contents = document.getElementById('view-' + req_id).innerHTML;
    const new_contents = document.getElementById(req_id + '-contents').value;
    const body = {
        'contents': new_contents
    }
    fetch('/requirement_set/'+req_set_id+'/'+req_id, {
        'method': 'POST',
        'headers': {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
    }).then((response) => {
        if (response.status == 200) {
            document.getElementById('view-' + req_id).innerHTML = new_contents;
            hide_requirement_editing(req_id);
        } else {
            alert("Something went wrong!")
        }
    });
}

function new_requirement(req_set_id, before, after) {
    const contents = document.getElementById('new-requirement-contents').value;
    const body = {
        'requirement': {
            'contents': contents
        },
        'before': before,
        'after': after
    };

    alert("hi")
    request = {
        'method': 'POST',
        'body': JSON.stringify(body),
        'headers': {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    };

    fetch('/requirement_set/'+req_set_id+'/add', request).then((response) => {
        alert("hi there")
        if (response.status == 200) {
            // location.reload();
        } else {
            alert("Something went wrong!");
        }
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

function copy_id(req_set_id, req_id) {
    navigator.clipboard.writeText(req_set_id + ':' + req_id);
}

function link_to(to_req_set_id, to_req_id) {
    read_link_id((from_req_set_id, from_req_id) => {
        link(from_req_set_id, from_req_id, to_req_set_id, to_req_id);
    });
}

function link_from(from_req_set_id, from_req_id) {
    read_link_id((to_req_set_id, to_req_id) => {
        link(from_req_set_id, from_req_id, to_req_set_id, to_req_id);
    });
}

function read_link_id(callback) {
    let combined_id = prompt('Paste requirement id here');
    console.log(combined_id);
    const parts = combined_id.split(':');
    console.log(parts);
    const req_set_id = parts[0];
    const id = parts[1];
    callback(req_set_id, id);
}

function link(from_req_set_id, from_req_id, to_req_set_id, to_req_id) {
    const body = {
        'from': {
            'requirement_set': from_req_set_id,
            'id': from_req_id
        },
        'to': {
            'requirement_set': to_req_set_id,
            'id': to_req_id
        }
    };
    request = {
        'method': 'POST',
        'body': JSON.stringify(body),
        'headers': {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
    };

    fetch('/link', request).then((response) => {
        if (response.status != 200) {
            alert("Something went wrong!");
        }
    });
}
