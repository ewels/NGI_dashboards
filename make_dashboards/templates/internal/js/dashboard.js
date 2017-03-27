
// Javascript for the NGI Stockholm Internal Dashboard

$(function () {

    try {

        Highcharts.setOptions({
            chart: {
                style: {
                    fontFamily:'"Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif'
                }
            }
        });

        // Header clock
        updateClock();

        // Format KPI update number
        $('#time_created').text(moment($('#time_created').text()).format("YYYY-MM-DD, HH:mm"));

        // Cron job runs on the hour, every hour. Get the web page to reload at 5 past the next hour
        var reloadDelay = moment().add(1, 'hours').startOf('hour').add(5, 'minutes').diff();
        setTimeout(function(){ location.reload(); }, reloadDelay );
        console.log("Reloading page in "+Math.floor(reloadDelay/(1000*60))+" minutes");

        // Collect data into shorter variable names
        tat = data['turnaround_times']
        tat_l = data['limits']['turnaround_times'];
        p_opened = data['projects']['opened_n_weeks_ago']
        p_closed = data['projects']['closed_n_weeks_ago']
        oc_labels = data['projects']['labels']
        pl = data['process_load']
        pl_l = data['limits']['process_load']
        suc = data['success_rate']

        // Top row
        make_tat_plot('#finished_proj_tat', 'finished_library_project', tat_l, tat, 'Finished Lib<br>'+Math.round(tat['finished_library_project'])+' days');
        make_tat_plot('#lp_proj_tats', 'library_prep_project', tat_l, tat, 'Prep Projects<br>'+Math.round(tat['library_prep_project'])+' days');
        make_tat_plot('#rc_tat', 'initial_qc', tat_l, tat);
        make_tat_plot('#lp_tat', 'library_prep', tat_l, tat);
        make_tat_plot('#seq_tat', 'sequencing', tat_l, tat);
        make_tat_plot('#bioinfo_tat', 'bioinformatics', tat_l, tat);

        // Middle row, projects openend / closed
        try {
            make_proj_open_close_plot(
                '#proj_openclose',
                [ p_opened['3'], p_opened['2'], p_opened['1'], p_opened['0'] ],
                [ p_closed['3']*-1, p_closed['2']*-1, p_closed['1']*-1, p_closed['0']*-1 ],
                // [ oc_labels['3'], oc_labels['2'], oc_labels['1'], oc_labels['0'] ]
                [ '3 weeks ago', '2 weeks ago', '1 week ago', 'this week' ]
            );
        } catch(err) {
            $('#proj_openclose').addClass('coming_soon').text('coming soon');
        }
        try {
            $('#projects-open-production').text(data['projects']['in_production']);
            $('#projects-open-applications').text(data['projects']['in_applications']);
        } catch(err) {
            console.log('Could not get number of opened and closed projects.')
        }

        // Middle Row - Queue plots
        // Max - 5 * pulse
        //
        sequencing_q_subtext=pl['miseq_sequencing_queue_l']+'<span style="color:#DF5353">M</span>,'+
            pl['hiseq_sequencing_queue_l']+'<span style="color:#55BF3B">H</span>,'+
            pl['hiseqX_sequencing_queue_l']+'<span style="color:#7cb5ec">X</span> lanes in queue';
        make_queue_plot('#lp_queue',      pl_l['library_prep'],   pl['library_prep_queue'],   pl['library_prep_queue']+' samples in queue');
        make_queue_plot('#seq_queue',     pl_l['sequencing_queue'],     [pl['miseq_sequencing_queue_l'], pl['hiseq_sequencing_queue_l'], pl['hiseqX_sequencing_queue_l']], sequencing_q_subtext);
        make_queue_plot('#bioinfo_queue', pl_l['bioinformatics'], pl['bioinformatics_queue'], pl['bioinformatics_queue']+' lanes in queue');

        // Middle Row - Balance plots
        sequencing_subtext=pl['miseq_sequencing_l']+'<span style="color:#AF2323">M</span>,'+
            pl['hiseq_sequencing_l']+'<span style="color:#258F0B">H</span>,'+
            pl['hiseqX_sequencing_l']+'<span style="color:#4c85bc">X</span> lanes in progress';
        make_balance_plot('#rc_finished_balance', pl_l['initial_qc_lanes'],   pl['initial_qc_lanes'],   undefined, pl['initial_qc_lanes']+' lanes in progress');
        console.log(pl['initial_qc_samples']);
        make_balance_plot('#rc_balance',          pl_l['initial_qc_samples'], pl['initial_qc_samples'], undefined, pl['initial_qc_samples']+' samples in progress');
        make_balance_plot('#lp_balance',          pl_l['library_prep'],       pl['library_prep'],       undefined, pl['library_prep']+' samples in progress');
        make_balance_plot('#seq_balance',         pl_l['sequencing'],         [pl['miseq_sequencing_l'], pl['hiseq_sequencing_l'], pl['hiseqX_sequencing_l']],         undefined, sequencing_subtext);
        make_balance_plot('#bioinfo_balance',     pl_l['bioinformatics'],     pl['bioinformatics'],     undefined, pl['bioinformatics']+' lanes in progress');

        // Bottom row
        make_success_plot('#rc_success', suc['initial_qc']*100);
        make_success_plot('#lp_success', suc['library_prep']*100);
        make_success_plot('#seq_success', suc['sequencing']*100);
        make_success_plot('#bioinfo_success', suc['bioinformatics']*100);

    } catch(err){
        $('.main-page').html('<div class="alert alert-danger text-center" style="margin: 100px 50px;"><p><strong>Error loading dashboard data</strong></p></div><pre style="margin: 100px 50px;"><code>'+err+'</code></pre>');
        console.log(err);
        // Try reloading in a few minutes
        setTimeout(function(){ location.reload(); }, 300000); // 5 minutes
    }

});


// Make a speedometer plot to show turnaround times
function make_tat_plot(target, k, tat_l, tat, title){
    try {
        var overTop = false;
        if(target === undefined){ throw 'Target missing'; }
        if(k === undefined){ throw 'Key missing'; }
        if(tat_l === undefined){ throw 'tat_l missing'; }
        if(tat === undefined){ throw 'tat missing'; }
        aim = tat_l[k];
        now = tat[k];
        ninetieth = tat[k+'_90th'];
        if(aim === undefined){ throw 'aim missing'; }
        if(now === undefined){ throw 'now missing'; }
        if(title === undefined){
            title = Math.round(now)+' days'
        }
        if(now > aim * 2.5){
            now = aim * 2.6;
            overTop = true;
        }
        $(target).highcharts({
            chart: {
                type: 'gauge',
                height: 120,
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
                center: ['50%', '170%'],
                size: 270
            },
            tooltip: { enabled: false },
            credits: { enabled: false },
            yAxis: {
                min: 0,
                max: aim * 2.5,
                minorTickWidth: 0,
                tickPosition: 'outside',
                tickPositions: [0, aim],
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
                name: '90th Percentile',
                data: [ninetieth],
            },{
                name: 'Turn Around Time',
                data: [now],
            }]
        },
        // Move needle if over limit
        function (chart) {
            if(overTop){
                var mul = 2.6
                setInterval(function () {
                    if(mul == 2.6){ mul = 2.52; }
                    else { mul = 2.6; }
                    chart.series[0].points[0].update(aim * mul, false);
                    chart.redraw();
                }, 200);
            }
        });
    } catch(err) {
        $(target).addClass('coming_soon').text('coming soon');
    }
}

function make_queue_plot(target, aim, now, subtext){
    try {
        if(target === undefined){ throw 'Target missing'; }
        if(aim === undefined){ throw 'aim missing'; }
        if(now === undefined){ throw 'now missing'; }
        if (!Array.isArray(now)){
            series=[now];
        }else{
            chroma_colors=chroma.scale(['#DF5353','#55BF3B','#7cb5ec']).colors(now.length);
            series=[];
            for (i in now){
                obj={name:'serie'+i,
                    color : chroma_colors[i], 
                    dataLabels: {enabled: true},
                    y:now[i]};
                series.push(obj);
            }
        }
        var max = aim * 5;
        $(target).highcharts({
            chart: {
                type: 'bar',
                height: 96,
                spacingBottom: 17,
                spacingTop: 7,
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
                max: max,
                tickInterval: aim,
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
                    color: '#7cb5ec',
                    states: { hover: { enabled: false } }
                },
            },
            legend: { enabled: false },
            credits: { enabled: false },
            tooltip: { enabled: false },
            series: [{
                name: 'Queue',
                data: series
            }]
        });
    } catch(err) {
        $(target).addClass('coming_soon').text('coming soon');
    }
}


// Function to make the load balancing plots
function make_balance_plot(target, aim, now, prev, subtext){
    try {
        if(target === undefined){ throw 'Target missing'; }
        if(aim === undefined){ throw 'aim missing'; }
        if(now === undefined){ throw 'now missing'; }
        if (!Array.isArray(now)){
            my_plotlines=[{
                    color: '#000',
                    width: 2,
                    value: now,
                    zIndex: 1000
                }];
        }else{
            my_plotlines=Array();
            chroma_colors=chroma.scale(['#AF2323','#259F0B','#4c85cc']).colors(now.length);
            pl=[];
            for (i in now){
                obj={name:'serie'+i,
                    color : chroma_colors[i], 
                    dataLabels: {enabled: true},
                    width: 2,
                    zIndex: 1000,
                    value: now[i]};
                my_plotlines.push(obj);
            }
        }
        $(target).highcharts({
            chart: {
                type: 'bar',
                height: 95,
                spacingBottom: 10,
                spacingTop: 0,
                backgroundColor:'rgba(255, 255, 255, 0.1)',
                plotBackgroundColor:'#ed8c83',
                plotBorderColor: '#FFFFFF',
                plotBorderWidth: 14
            },
            xAxis: {
                categories: ['Queue'],
                title: { text: null },
                labels: { enabled: false },
                tickWidth: 0,
                lineWidth: 0
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
                    color: '#8ad88b',
                    from: aim,
                    to: aim * 4
                }],
                plotLines: my_plotlines
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
            }],
            title: { text: null },
            legend: { enabled: false },
            credits: { enabled: false },
            series: [
                { data: [0] },
                { data: [0], yAxis: 1 }
            ]
        });
    } catch(err) {
        console.log(err);
        $(target).addClass('coming_soon').text('coming soon');
    }
}


function make_proj_open_close_plot(target, opened, closed, categories){
    try {
        if(target === undefined){ throw 'Target missing'; }
        if(opened === undefined){ throw 'opened missing'; }
        if(closed === undefined){ throw 'closed missing'; }
        if(categories === undefined){ throw 'categories missing'; }
        $(target).highcharts({
            chart: {
                type: 'column',
                backgroundColor:'rgba(255, 255, 255, 0.1)',
                height: 240,
                spacingBottom: 0,
            },
            title: { text: null },
            credits: { enabled: false },
            tooltip: { enabled: false },
            xAxis: [{
                categories: categories,
                reversed: false,
                labels: {
                    step: 1,
                    rotation: -45,
                }
            }],
            yAxis: {
                title: {
                    text: '#Projects'
                },
                allowDecimals: false,
                // minorTickInterval: 1
            },
            plotOptions: {
                series: {
                    stacking: 'normal',
                    states: { hover: { enabled: false } }
                }
            },
            legend: {
                reversed: true,
                floating: true,
                layout: 'horizontal',
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
    } catch(err) {
        $(target).addClass('coming_soon').text('coming soon');
    }

}

// Make an arc plot to show percentage success
function make_success_plot(target, now){
    try {
        if(target === undefined){ throw 'Target missing'; }
        if(isNaN(now)){ throw 'now missing'; }
        $(target).highcharts({
            chart: {
                type: 'solidgauge',
                backgroundColor:'rgba(255, 255, 255, 0.1)',
                height: 140
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
                center: ['50%', '88%'],
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
                dataLabels: { format: '<div style="text-align:center; font-size:25px; color:black; font-weight: normal;">{y:,.0f}%</div>' },
            }]
        });
    } catch(err) {
        $(target).addClass('coming_soon').text('coming soon');
    }
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

    var updated = moment($('#time_created').data('original'));
    $('#report_age').text( moment().from(updated, true) );
    setTimeout(updateClock, 1000);
}

