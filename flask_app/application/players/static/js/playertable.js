$(document).ready(function () {
    buildTable(players,'player_table');
})

async function buildTable(players,table) {
    $(table).DataTable( {
        "destroy": true,
        "info": false,
        "searching": false,
        "order": [[ 1, 'dsc' ]],
        "lengthMenu": [ [5, 10, 25, 50, -1], [5, 10, 25, 50, "All"] ],
        data: players,
        columns: [
            { data: 'player' },
            { data: 'team' },
            { data: 'hand' },
            { data: 'ppos' },
            { data: 'spos' }
        ]
    } );
}