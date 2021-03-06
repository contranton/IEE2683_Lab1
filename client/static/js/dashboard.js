

// Horizontal size of the plot window
var T_SIZE = 10000;

var DELAY_PER_REDRAW = 0;

// Data arrays (independent from plotting) to be updated from live data
// Need to be explicitly declared to work with TimeChart
const zero = [];
var ref_h1_arr = [];
var ref_h2_arr = [];

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
var is_controling = false;

var ref_h1 = 0;
var ref_h2 = 0;

// Pointers to the sine interval
var sines = {};

// on activate sine (setInterval?)
sine = function(id, freq, amp, off){
    // performance.now is in ms and we're measuring in s!
    value = amp*Math.sin(2*Math.PI*freq*performance.now()/1000 + off);
    socket.emit('user-input', {id: 'voltage' + id, val: value});
}

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
        $("#pid-div").hide();
        $("#ctrl-div").show();
        is_controling = true;
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
        is_controling = false;
        $("#ctrl-div").hide();
        $("#pid-div").show();
        $("#ctrl-mode").prop('value', window._oldbtntext);
    })

    // Control actions

    $("#ctrl-mode").click(function () {
        socket.emit('ctrl-mode');
        $("#control-ui").show();
    })

    $("#tab-fixed").click(function(){
        $("#ctrl-div").find("#ctrl-fixed").show();
        $("#ctrl-div").find("#ctrl-sine").hide();
    })

    $("#tab-sine").click(function(){
        $("#ctrl-div").find("#ctrl-fixed").hide();
        $("#ctrl-div").find("#ctrl-sine").show();
    })

    update_sine = function(id){
        freq =   parseFloat($("#" + id + "-sine-freq").val());
        amp =    parseFloat($("#" + id + "-sine-amp").val());
        offset = parseFloat($("#" + id + "-sine-offset").val());
        send_freq = 10*freq; // Send samples at 5x the Nyquist frequency
        sines[id] = setInterval(sine, send_freq, id[1], freq, amp, offset);
    }

    $("[id*=sine-on]").click(function(){
        id = $(this).attr('id').slice(0, 2); // v2-sine-on -> v2

        // If sine already happening, stop it
        if(sines[id] != null){
            clearInterval(sines[id]);
            $(this).attr('value', "Activar");
            sines[id] = null;

        // Else, start the sine
        }else{
            $(this).attr('value', "Stop");
            update_sine(id);
        }
    })

    $("#ctrl-sine").find("input:not([id*=on])").change(function(){
        id = $(this).attr('id').slice(0, 2); // v2-sine-on -> v2
        if(sines[id]!=null){
            clearInterval(sines[id]);
            update_sine(id);
        }
    })

    $("#voltage1-slider").on('input', function (){
        $("#voltage1-text").attr('value', $(this).val());
    })

    $("#voltage2-slider").on('input', function (){
        $("#voltage2-text").attr('value', $(this).val());
    })

    $("#voltage1-zero").click(function(){
        $("#voltage1-text").attr('value', 0);
        $("#voltage1-slider").val(0);
    })

    $("#voltage2-zero").click(function(){
        $("#voltage2-text").attr('value', 0);
        $("#voltage2-slider").val(0);
    })

    $("#params-div").find("gamma").on('input', function(){
        if($(this).val() > $(this).attr('max')){
            $(this).val($(this).attr('max'))
        }else if($(this).val() < $(this).attr('min')){
            $(this).val($(this).attr('min'))
        }
    })

    // Handle data stream from the server
    var n_redraw = {};
    socket.on('server_push', function (msg) {
        var dat = msg.data

        // Plot variables
        for (const [variable, value] of Object.entries(dat.data)) {
            // Update data_store
            var t_ = performance.now() - T_SIZE;
            data_store[variable].push({ x: t_, y: value });
            ref_h1_arr.push({ x: t_, y: ref_h1 });
            ref_h2_arr.push({ x: t_, y: ref_h2 });
            zero.push({ x: t_, y: 0 });

            // Update plot
            if(n_redraw[variable] === undefined){ n_redraw[variable] = 0;}
            if(++n_redraw[variable] > DELAY_PER_REDRAW){
                plots[variable].plot.update();
                n_redraw[variable] = 0;
            }

        }

        // Set alarms
        for (var [tank, state] of Object.entries(msg.alarms)){
            tank = "#" + tank;
            if(state.on){
                $("#alarm-container").find(tank).attr("state", "bad");
                $("#alarm-container").find(tank).find("h3").text("h < 10cm!!");
            }else{
                $("#alarm-container").find(tank).attr("state", "good");
                $("#alarm-container").find(tank).find("h3").text("Altura bien");
            }
        }
    })

    update_users = function(usrs){
        $('#users').html("<ul></ul>")
        console.log("Updating users")
        for (var user of usrs) {
            $('#users').append("<li>" + user + "</li>")
        }
    }

    // Get state from server
    socket.on('system-state', function(msg){
        msg = JSON.parse(msg);
        update_users(msg.users);
        $("#h1-reference").val(msg.params.h1_ref); ref_h1 = msg.params.h1_ref;
        $("#h2-reference").val(msg.params.h2_ref); ref_h2 = msg.params.h2_ref;
        $("#gamma1").val(msg.params.g1);
        $("#gamma2").val(msg.params.g2);
        $("#Kp-gain").val(msg.params.Kp);
        $("#Ki-gain").val(msg.params.Ki);
        $("#Kd-gain").val(msg.params.Kd);
        $("#pid-on").prop("checked", msg.params.pid_on);
        $("#antiwindup-on").prop("checked", msg.params.antiwindup);
    })

    // Send all inputs to server
    // TODO: Dual of this function but with data sent by the server
    var foo = function(){
        var value;
        var id_ = $(this).attr('id');

        if($(this).is(":checkbox")){
            // Cast to boolean
            value = $(this).is(":checked");
        }else if($(this).is("select")){
            // Get string value
            value = $(this).val();
        }else if($(this).is(":button")){
            // Voltage buttons are always to set voltage 0
            if($(this).attr("id").includes("voltage")) {value = 0};
        }else{
            // Cast to float
            value = parseFloat($(this).val());
            try{
                if(id_.includes("voltage")){
                    id_ = id_.slice(0, id_.indexOf("-"));
                }
            }catch(error){}
        }
        if(isNaN(value)) return;


        var data = {id:id_, val:value}
        socket.emit("user-input", data)
    };

    // Assign to ALL DEM INPUTS
    $("input:not([id*=sine])").on('input', foo);
    $("input:button:not([id*=sine])").on('click', foo);
    $("select:not([id*=sine])").on('change', foo);

    //Options
    $("#refresh-rate").change(function(){
        var choice = $(this).children("option:selected").val();
        switch(choice){
            case "fast": DELAY_PER_REDRAW = 0; break;
            case "med":  DELAY_PER_REDRAW = 10; break;
            case "slow": DELAY_PER_REDRAW = 100; break;
        }
    })

    $("#plot-window").change(function(){
        T_SIZE = parseFloat($(this).val());
        for(var dat of Object.values(plots)){
            dat.plot.options.xRange.max = T_SIZE;
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

        if(variable == "h1"){
            plot.options.series.push({name: "Reference", color:"#000000", lineWidth: 1, data: ref_h1_arr});
        }else if (variable == "h2"){
            plot.options.series.push({name: "Reference", color:"#000000", lineWidth: 1, data: ref_h2_arr});
        }

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
