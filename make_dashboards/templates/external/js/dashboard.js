
// Javascript for the NGI Stockholm Internal Dashboard

var plot_height = 415;

$(function () {
    
    try {
    
        Highcharts.setOptions({
            colors: ['#377eb8','#4daf4a','#984ea3','#ff7f00','#a65628','#f781bf','#999999','#e41a1c'],
            chart: {
                style: {
                    fontFamily:'"Roboto", "Helvetica Neue", Helvetica, Arial, sans-serif'
                }
            }
        });
        
        // Header clock
        updateClock();
        
        // Cron job runs on the hour, every hour. Get the web page to reload at 5 past the next hour
        var reloadDelay = moment().add(1, 'hours').startOf('hour').add(5, 'minutes').diff();
        setTimeout(function(){ location.reload(); }, reloadDelay );
        console.log("Reloading page in "+Math.floor(reloadDelay/(1000*60))+" minutes");
        
        // # Projects plot
        var years = Object.keys(data['num_projects']).sort().reverse();
        var ydata = data['num_projects'][years[0]];
        make_bar_plot('#num_projects_plot', ydata, '# Projects in '+years[0]);
        
        // # Samples plot
        var years = Object.keys(data['num_samples']).sort().reverse();
        var ydata = data['num_samples'][years[0]];
        make_bar_plot('#num_samples_plot', ydata, '# Samples in '+years[0]);
        
        // Open Projects plot
        var ydata = data['open_projects'];
        make_bar_plot('#open_projects_plot', ydata, '# Open Projects ');
        
        // Delivery times plot
        make_delivery_times_plot();
        
        // Affiliations plot
        make_affiliations_plot();
        
        // Throughput plot
        make_throughput_plot();
        
    } catch(err){
        $('.main-page').html('<div class="alert alert-danger text-center" style="margin: 100px 50px;"><p><strong>Error loading dashboard data</strong></p></div><pre style="margin: 100px 50px;"><code>'+err+'</code></pre>');
        console.log(err);
        // Try reloading in a few minutes
        setTimeout(function(){ location.reload(); }, 300000); // 5 minutes
    }
    
});


// Make a bar plot
function make_bar_plot(target, ydata, title){
    try {
        if(target === undefined){ throw 'Target missing'; }
        if(ydata === undefined){ throw 'Data missing'; }
        if(title === undefined){ title = null; }
        
        var cats = Object.keys(ydata).sort(function(a,b){return ydata[a]-ydata[b]}).reverse();
        var sorted_ydata = Array();
        var nice_cats = Array();
        var total_count = 0;
        for(j=0; j<cats.length; j++){
            if(data['key_names'][cats[j]] == undefined){
                nice_cats.push(cats[j]);
            } else {
                nice_cats.push(data['key_names'][cats[j]]);
            }
            sorted_ydata.push(ydata[cats[j]]);
            total_count += ydata[cats[j]];
        }
        
        $(target).highcharts({
            chart: {
                type: 'bar',
                height: plot_height,
                plotBackgroundColor: null,
            },
            title: {
                text: title,
                style: { 'font-size': '24px' }
            },
            subtitle: {
                text: 'Total: '+total_count
            },
            tooltip: { enabled: false },
            credits: { enabled: false },
            xAxis: {
                categories: nice_cats
            },
            yAxis: {
                min: 0,
                title: { text: null }
            },
            legend: { enabled: false },
            plotOptions: {
                bar: {
                    animation: false,
                    borderWidth: 0,
                    groupPadding: 0.1,
                    dataLabels: { enabled: true }
                },
            },
            series: [{ data: sorted_ydata }]
        });
    } catch(err) {
        $(target).addClass('coming_soon').text('coming soon');
        console.log(err);
    }
}


function make_delivery_times_plot(){
    var years = Object.keys(data['delivery_times']).sort().reverse();
    var ydata = data['delivery_times'][years[0]];
    var ykeys = Object.keys(ydata).sort(function(a,b){ return a.match(/\d+/)-b.match(/\d+/) });
    var pdata = Array();
    for(i=0; i<ykeys.length; i++){ pdata.push([ykeys[i], ydata[ykeys[i]]]); }
    
    $('#delivery_times_plot').highcharts({
        chart: {
            plotBackgroundColor: null,
            plotBorderWidth: 0,
            plotShadow: false,
            height: plot_height,
        },
        title: {
            text: 'Delivery Times in '+years[0],
            style: { 'font-size': '24px' }
        },
        subtitle: {
            text: 'Projects started this year'
        },
        tooltip: { enabled: false },
        credits: { enabled: false },
        plotOptions: {
            pie: {
                // dataLabels: { enabled: false },
                dataLabels: {
                    enabled: true,
                    formatter: function() {
                        return Math.round(this.percentage*100)/100 + ' %';
                    },
                    distance: -40,
                    style: {
                        fontWeight: 'bold',
                        color: 'white',
                        textShadow: '0px 1px 2px black',
                        'font-size': '18px'
                    }
                },
                showInLegend: true,
                startAngle: -90,
                endAngle: 90,
                size: '120%',
                center: ['50%', '75%']
            }
        },
        legend: {
            enabled: true,
            floating: true,
            y: -20
        },
        series: [{
            type: 'pie',
            name: 'Delivery Times',
            innerSize: '50%',
            data: pdata
        }]
    });
}


function make_affiliations_plot(){
    var years = Object.keys(data['project_user_affiliations']).sort().reverse();
    var ydata = data['project_user_affiliations'][years[0]];
    var ykeys = Object.keys(ydata).sort(function(a,b){return ydata[a]-ydata[b]}).reverse();
    var pdata = Array();
    for(i=0; i<ykeys.length; i++){
        var thiskey = ykeys[i];
        if(data['key_names'][thiskey] != undefined){
            thiskey = data['key_names'][thiskey];
        }
        pdata.push([thiskey, ydata[ykeys[i]]]);
        
    }
    
    $('#affiliations_plot').highcharts({
        chart: {
            plotBackgroundColor: null,
            height: plot_height,
            type:'pie'
        },
        title: {
            text: 'Project Affiliations in '+years[0],
            style: { 'font-size': '24px' }
        },
        tooltip: { enabled: false },
        credits: { enabled: false },
        plotOptions: {
            pie: {
                dataLabels: { enabled: false },
                showInLegend: true,
            }
        },
        legend: {
            enabled: true,
            layout: 'vertical',
            align: 'right',
            verticalAlign: 'top',
            y: 100,
            itemStyle: {
                'font-size': '12px',
                'font-weight': 'normal'
            }
        },
        series: [{ data: pdata }]
    });
}


function make_throughput_plot(){
    var num_weeks = 12;
    var weeks = Object.keys(data['bp_seq_per_week']).sort().reverse().slice(0,num_weeks+1).reverse();
    var skeys = Array('HiseqX', 'Hiseq', 'Miseq');
    // Collect all series types
    for(i=0; i<num_weeks; i++){
        var wkeys = Object.keys(data['bp_seq_per_week'][weeks[i]]);
        for(j=0; j<wkeys.length; j++){
            if(skeys.indexOf(wkeys[j]) == -1){
                skeys.push(wkeys[j]);
            }
        }
    }
    // Collect the data
    var sdata = Array();
    for(j=0; j<skeys.length; j++){
        var swdata = Array();
        for(i=0; i<num_weeks; i++){
            thisdata = data['bp_seq_per_week'][weeks[i]][skeys[j]];
            swdata.push(thisdata == undefined ? 0 : thisdata);
        }
        sdata.push({
            name: skeys[j],
            data: swdata
        });
    }
    
    $('#throughput_plot').highcharts({
        chart: {
            plotBackgroundColor: null,
            height: plot_height,
            type: 'area'
        },
        title: {
            text: 'Sequencing Throughput'
        },
        subtitle: {
            text: 'Base pairs sequenced in the past twelve weeks'
        },
        xAxis: {
            labels: {
                formatter: function() {
                    return weeks[this.value];
                },
                rotation: -30,
            },
            tickInterval: 1,
            title: { enabled: false },
        },
        yAxis: {
            title: { text: null },
            labels: {
                formatter: function () {
                    return this.value.toExponential();
                }
            }
        },
        tooltip: { enabled: false },
        credits: { enabled: false },
        plotOptions: {
            area: {
                stacking: 'normal',
                lineColor: '#999999',
                lineWidth: 1,
                marker: { enabled: false }
            }
        },
        legend: {
            enabled: true,
            floating: true,
            layout: 'vertical',
            align: 'left',
            verticalAlign: 'top',
            y: 60,
            x: 70,
            itemStyle: { 'font-weight': 'normal' },
            borderWidth: 1,
            backgroundColor: ((Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF'),
            shadow: true
        },
        series: sdata
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
    
    var updated = moment($('#date_rendered').text());
    $('#report_age').text( moment().from(updated, true) );
    setTimeout(updateClock, 1000);
}

