
// Javascript for the NGI Stockholm Internal Dashboard

$(function () {
    
    Highcharts.setOptions({
        chart: {
            style: {
                fontFamily:'"Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif'
            }
        }
    });
    
    // Header clock
    updateClock();
    
    // Top row
    make_tat_plot('#finished_proj_tat', 14, 12, 'Finished<br>Libraries');
    make_tat_plot('#lp_proj_tats', 28, 28, 'Library Preps');
    make_tat_plot('#rc_tat', 14, 9, 9+' days');
    make_tat_plot('#lp_tat', 19, 18, 18+' days');
    make_tat_plot('#seq_tat', 13, 31, 31+' days');
    make_tat_plot('#bioinfo_tat', 10, 8, 8+' days');
    
    // Middle row, projects openend / closed
    make_proj_open_close_plot('#proj_openclose', [110,63,14,19], [-29,-16,-94,-43], ['Oct-26','Nov-02','Nov-09','Nov-16']);
    
    // Middle Row - Queue plots
    make_queue_plot('#rc_queue', 100, 26, 26+' projects');
    make_queue_plot('#lp_queue', 100, 48, 48+' samples');
    make_queue_plot('#seq_queue', 100, 94, 94+' lanes');
    make_queue_plot('#bioinfo_queue', 100, 57, 57+' lanes');
    
    // Middle Row - Balance plots
    make_balance_plot('#rc_balance', 200, 326, 452, 326+' samples');
    make_balance_plot('#lp_balance', 200, 178, 332, 178+' samples');
    make_balance_plot('#seq_balance', 50, 121, 128, 121+' lanes');
    make_balance_plot('#bioinfo_balance', 50, 57, 92, 57+' lanes');
    
    // Bottom row
    make_success_plot('#rc_success', 73);
    make_success_plot('#lp_success', 65);
    make_success_plot('#seq_success', 87);
});


// Make a speedometer plot to show turnaround times
function make_tat_plot(target, aim, now, title){
    $(target).highcharts({
        chart: {
            type: 'gauge',
            height: 100,
            backgroundColor:'rgba(255, 255, 255, 0.1)'
        },
        title: {
            text: title,
            floating: true,
            y: 60
        },
        pane: {
            startAngle: -45,
            endAngle: 45,
            background: null,
            center: ['50%', '200%'],
            size: 250
        },
        tooltip: { enabled: false },
        credits: { enabled: false },
        yAxis: {
            min: 0,
            max: aim * 2.5,
            minorTickWidth: 0,
            tickPosition: 'outside',
            tickInterval: aim,
            labels: {
                rotation: 'auto',
                distance: 20
            },
            plotBands: [{
                from: 0,
                to: aim,
                color: '#55BF3B',
                innerRadius: '100%',
                outerRadius: '105%'
            },
            {
                from: aim,
                to: aim * 2,
                color: '#DDDF0D',
                innerRadius: '100%',
                outerRadius: '105%'
            },
            {
                from: aim * 2,
                to: aim * 3,
                color: '#DF5353',
                innerRadius: '100%',
                outerRadius: '105%'
            }]
        },
        plotOptions: {
            gauge: {
                dataLabels: { enabled: false },
                dial: { radius: '100%' }
            }
        },
        series: [{
            name: 'Turn Around Time',
            data: [now],
        }]
    });
}

function make_queue_plot(target, max, now, subtext){
    var f = chroma.scale('PuBu');
    var col = f(now/max).css();
    $(target).highcharts({
        chart: {
            type: 'bar',
            height: 80,
            spacingBottom: 0,
            spacingTop: 0,
            backgroundColor:'rgba(255, 255, 255, 0.1)',
            plotBackgroundColor:'#f2f2f2',
        },
        xAxis: {
            categories: ['Queue'],
            title: { text: null },
            labels: { enabled: false },
            tickWidth: 0
        },
        yAxis: [{
            min: 0,
            max: 100,
            title: { text: null },
            opposite: true,
            labels: {
                y: -3,
                overflow: 'justify'
            }
        },{
            title: {
                text: subtext,
                y: 5,
                style: { 'font-size': 14 }
            }
        }],
        title: { text: null },
        plotOptions: {
            series: {
                pointPadding: 0,
                groupPadding: 0,
                color: col
            },
        },
        legend: { enabled: false },
        credits: { enabled: false },
        series: [{
            name: 'Queue',
            data: [now]
        }]
    });
}


// Function to make the load balancing plots
function make_balance_plot(target, aim, now, prev, subtext){
    $(target).highcharts({
        chart: {
            type: 'bar',
            height: 80,
            spacingBottom: 0,
            spacingTop: 0,
            backgroundColor:'rgba(255, 255, 255, 0.1)',
            plotBackgroundColor:'#f4c8c5',
        },
        xAxis: {
            categories: ['Queue'],
            title: { text: null },
            labels: { enabled: false },
            tickWidth: 0
        },
        yAxis: [{
            min: 0,
            max: aim * 5,
            title: { text: null },
            opposite: true,
            labels: {
                y: -3,
            },
            tickPositions: [ 0, aim, aim * 4, aim * 5 ],
            plotBands: [{
                color: '#d5f6ba',
                from: aim,
                to: aim * 4
            }],
            plotLines: [{
                color: '#000',
                width: 2,
                value: now,
                zIndex: 1000
            }]
        },{
            min: 0,
            max: aim * 5,
            title: {
                text: subtext,
                y: 5,
                style: { 'font-size': 14 }
            },
            labels: { enabled: false },
            gridLineWidth: 0,
            plotLines: [{
                color: '#999',
                width: 1,
                value: prev,
                zIndex: 1000
            }]
        }],
        title: { text: null },
        legend: { enabled: false },
        credits: { enabled: false },
        series: [
            { data: [0] },
            { data: [0], yAxis: 1 }
        ]
    });
}


function make_proj_open_close_plot(target, opened, closed, categories){
    $(target).highcharts({
        chart: {
            type: 'column',
            backgroundColor:'rgba(255, 255, 255, 0.1)',
            height: 200,
            spacingBottom: 0,
        },
        title: { text: null },
        credits: { enabled: false },
        xAxis: [{
            categories: categories,
            reversed: false,
            labels: {
                step: 1
            }
        }],
        yAxis: {
            title: {
                text: '#Projects'
            }
        },
        plotOptions: {
            series: {
                stacking: 'normal'
            }
        },
        legend: {
            reversed: true,
            floating: true,
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'top',
            labelFormat: '<span style="font-weight: 300;">{name}</span>',
            useHTML: true
        },
        series: [{
            name: 'Closed',
            data: closed
        }, {
            name: 'Opened',
            data: opened
        }]
    });
}

// Make an arc plot to show percentage success
function make_success_plot(target, now){
    $(target).highcharts({
        chart: {
            type: 'solidgauge',
            backgroundColor:'rgba(255, 255, 255, 0.1)',
            height: 180
        },
        title: null,
        pane: {
            startAngle: -90,
            endAngle: 90,
            background: {
                backgroundColor: '#EEE',
                innerRadius: '60%',
                outerRadius: '100%',
                shape: 'arc'
            },
            center: ['50%', '70%'],
            size: 200
        },
        tooltip: { enabled: false },
        credits: { enabled: false },

        // the value axis
        yAxis: {
            stops: [
                [0.1, '#DF5353'], // green
                [0.5, '#DDDF0D'], // yellow
                [0.9, '#55BF3B'] // red
            ],
            lineWidth: 0,
            minorTickInterval: null,
            tickPixelInterval: 400,
            tickWidth: 0,
            labels: {
                enabled: false
            },
            min: 0,
            max: 100
        },
        plotOptions: {
            solidgauge: {
                dataLabels: {
                    y: -40,
                    borderWidth: 0,
                    useHTML: true
                }
            }
        },
        series: [{
            name: 'Success Rate',
            data: [now],
            dataLabels: { format: '<div style="text-align:center; font-size:25px; color:black; font-weight: normal;">{y}%</div>' },
        }]
    });
}

function updateClock(){
    var now = moment(),
        second = now.seconds() * 6,
        minute = now.minutes() * 6 + second / 60,
        hour = ((now.hours() % 12) / 12) * 360 + 90 + minute / 12;

    $('#hour').css("transform", "rotate(" + hour + "deg)");
    $('#minute').css("transform", "rotate(" + minute + "deg)");
    $('#second').css("transform", "rotate(" + second + "deg)");
    $('#clock_time').text( moment().format('HH:mm') );
    $('#clock_date').text( moment().format('dddd Do MMMM') );
    setTimeout(updateClock, 1000);
}