
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
    
    // Top Row
    make_bar_plot('#lp_queue', [], [], 'green');
    make_bar_plot('#seq_queue', [], [], 'blue');
    make_bar_plot('#analysis_queue', [], [], 'blue');
    
    // Bottom row
    make_bar_plot('#user_affiliations', [], [], 'green');
    make_bar_plot('#throughput_plot', [], [], 'green');
    delivery_times_plot('#delivery_times', 80);
    seq_yield_plot('#seq_yield');
    
});


function make_bar_plot(target, data, categories, colour){
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
            data: data
        }, {
            name: 'Opened',
            data: data
        }]
    });
}

// Make an arc plot to show percentage success
function delivery_times_plot(target, now){
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

function seq_yield_plot(){
    
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