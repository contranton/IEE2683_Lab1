// TODO: Handle refreshing

// Horizontal size of the plot window
var T_SIZE = 10000;

//  How many new datapoints to receive until a redraw (helps performance)
var DELAY_PER_REDRAW = 0;

// Data arrays (independent from plotting) to be updated from live data
// Need to be explicitly declared to work with TimeChart
const zero = [];

// Addressable data-store
const data_store = {
    "t": [],
    "h1": [],
    "h2": [],
    "h3": [],
    "h4": [],
    "v1": [],
    "v2": []
}

// Plots container
plots = {
    "h1":{title: "Tanque 1",   color: "#666699" },
    "h2":{title: "Tanque 2",   color: "#669966"},
    "h3":{title: "Tanque 3",   color: "#226666"},
    "h4":{title: "Tanque 4",   color: "#996699"},
    "v1":{title: "Valvula 1", color: "#DD6677"},
    "v2":{title: "Valvula 2", color: "#EE8833"}
}

////////////////////////////////////////////////////////////////////////
// Document creation and callbacks

var ID = 0;
var socket;
var username;

$(document).ready(function () {
    socket = io("http://" + document.domain + ":" + location.port + "/dashboard");

    // Basic connections
    socket.on('connect', function () {
        socket.emit('client_connect');
    });

    $(window).on('beforeunload', function () {
        socket.emit('client_disconnect');
    });

    $(window).on('unload', function () {
        socket.emit('client_disconnect');
    });

    socket.on("server_force-disconnect", function(){
        console.log("Server stopped");
        alert("Server stopped!");
        window.location.href = "login";
    })

    socket.on('server_user-login', function (msg) {
        console.log("WUUUUT")
        var can_control = msg.data.can_control;
        $("#ctrl-mode").attr('disabled', !can_control);
        if(!can_control){
            $("#ctrl-mode").prop("value", msg.data.editor + " está editando");
        }
    });

    // TODO: Toggle all necessary inputs
    socket.on('server_disable-ctrl', function (who) {
        $("#ctrl-mode").attr('disabled', true);
        $("#ctrl-mode").prop("value", who + " está editando");
    });

    socket.on('server_enable-ctrl', function () {
        $("#ctrl-mode").attr('disabled', false);
        $("#ctrl-mode").prop("value", "Control Manual");
    });

    socket.on('server_user-begin-ctrl', function(){
        $("#ctrl-div").show();
        window._oldbtntext = $("#ctrl-mode").prop('value');
        $("#ctrl-mode").prop('value', "Finalizar");

        var v1 = data_store.v1[data_store.v1.length - 1].y;
        $("#voltage1-slider").attr('value', v1);
        $("#voltage1-text").attr('value', v1);

        var v2 = data_store.v2[data_store.v2.length - 1].y;
        $("#voltage2-slider").attr('value', v2);
        $("#voltage2-text").attr('value', v2);
    })

    socket.on('server_user-end-ctrl', function(){
        $("#ctrl-div").hide();
        $("#ctrl-mode").prop('value', window._oldbtntext);
    })

    // Control actions
    $("#voltage1-slider").on('input', function (){
        $("#voltage1-text").attr('value', $(this).val());
        socket.emit('client_set-voltage1', parseFloat($(this).val()));
    })

    $("#voltage2-slider").on('input', function (){
        $("#voltage2-text").attr('value', $(this).val());
        socket.emit('client_set-voltage2', parseFloat($(this).val()));
    })

    // Server-pushed data
    socket.on('server_userlist', function (msg) {
        $('#users').html("<ul></ul>")
        console.log("Updating users")
        var usrs = JSON.parse(msg.data);
        for (var user of usrs) {
            $('#users').append("<li>" + user + "</li>")
        }
    });

    var n_redraw = {};
    socket.on('server_push', function (msg) {
        var dat = msg.data
        // For each variable
        for (const [variable, value] of Object.entries(dat.data)) {
            // Update data
            var t_ = performance.now() - T_SIZE;
            data_store[variable].push({ x: t_, y: value });
            zero.push({ x: t_, y: 0 });

            // Update plot
            if(n_redraw[variable] === undefined){ n_redraw[variable] = 0;}
            if(++n_redraw[variable] > DELAY_PER_REDRAW){
                plots[variable].plot.update();
                n_redraw[variable] = 0;
            }

        }
    })

    // Button callbacks
    $("#ctrl-mode").click(function () {
        socket.emit('ctrl-mode');
        $("#control-ui").show();
    })

    // Options
    $("#refresh-rate").change(function(){
        var choice = $(this).children("option:selected").val();
        switch(choice){
            case "fast": DELAY_PER_REDRAW = 0; break;
            case "med":  DELAY_PER_REDRAW = 30; break;
            case "slow": DELAY_PER_REDRAW = 120; break;
        }
    })
})

///////////////////////////////////////////////////////////////////////////////////
// Create the plots and manage data

// Generate plot handles
for (var [variable, dat] of Object.entries(plots)) {

    var div = document.getElementById(variable);
    const plot = new TimeChart(div,
        {
            baseTime: Date.now(),
            series: [{
                name: dat.title,
                color: dat.color,
                data: data_store[variable]
            }, {
                name: "Origin",
                color: '#FF0000',
                lineWidth: 1,
                data: zero
            }],
            realTime: true,
            visible: true,
            lineWidth: 3,
            xRange: { min: 0, max: T_SIZE },
        });
    // Store plot handle in database
    plots[variable].plot = plot;
}

// Hide Plot legends
$('.chart').each(function (i, el) {
    var sR = el.shadowRoot;
    var v = el.id;
    var title = plots[v].title;
    var color = plots[v].color;
    var style = "text-align:center;font-style:italic;font-size:10;margin-top:0;color:" + color;
    $(sR).find('chart-legend').attr("hidden", true);
    $(sR).append("<h4 style='" + style + "'>" + title + "</h4>");
})
