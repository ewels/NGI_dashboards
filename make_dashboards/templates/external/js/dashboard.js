
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
            },
            plotOptions: { series: { animation: false } }
        });
        
        // Header clock
        updateClock();
        
        // Cron job runs on the hour, every hour. Get the web page to reload at 5 past the next hour
        var reloadDelay = moment().add(1, 'hours').startOf('hour').add(5, 'minutes').diff();
        setTimeout(function(){ location.reload(); }, reloadDelay );
        console.log("Reloading page in "+Math.floor(reloadDelay/(1000*60))+" minutes");
        
        // Check that the returned data is ok
        if ('error_status' in data){
            $('.mainrow').html('<div class="alert alert-danger text-center" style="margin: 100px 50px;"><p><strong>Error loading dashboard data (API)</strong><br>'+data['page_title']+': '+data['error_status']+' ('+data['error_reason']+')</p></div><pre style="margin: 100px 50px;"><code>'+data['error_exception']+'</code></pre>');
            console.log(data['error_reason']);
            console.log(data['error_status']);
            console.log(data['page_title']);
            console.log(data['error_exception']);
            // Try reloading in a few minutes
            setTimeout(function(){ location.reload(); }, 60000); // 1 minute
            return false;
        }
        
        // Projects plot
        var years = Object.keys(data['num_projects']).sort().reverse();
        var ydata = data['num_projects'][years[0]];
        make_bar_plot('#num_projects_plot', ydata, '# Projects in '+years[0]);
        
        // Samples plot
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
        $('.mainrow').html('<div class="alert alert-danger text-center" style="margin: 100px 50px;"><p><strong>Error loading dashboard data</strong></p></div><pre style="margin: 100px 50px;"><code>'+err+'</code></pre>');
        console.log(err);
        // Try reloading in a few minutes
        setTimeout(function(){ location.reload(); }, 60000); // 1 minute
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
    var ydata_fl = data['delivery_times_finishedlib'][years[0]];
    var ykeys = Object.keys(ydata).sort(function(a,b){ return a.match(/\d+/)-b.match(/\d+/) });
    var pdata = Array();
    for(i=0; i<ykeys.length; i++){
        num_fl = ydata_fl[ykeys[i]];
        num_inhouse = ydata[ykeys[i]] - num_fl;
        pdata.push({
            'name': ykeys[i],
            'data': [num_fl, num_inhouse]
        });
    }
    var d = new Date();
    
    $('#delivery_times_plot').highcharts({
        chart: {
            plotBackgroundColor: null,
            plotBorderWidth: 0,
            plotShadow: false,
            height: plot_height,
            type: 'bar'
        },
        title: {
            text: 'Delivery Times in '+years[0],
            style: { 'font-size': '24px' }
        },
        subtitle: {
            text: 'Projects started '+d.getFullYear()
        },
        credits: { enabled: false },
        tooltip: {
            headerFormat: '',
            pointFormat: '<span style="color:{point.color}; font-weight:bold;">{point.name}eeks</span>: {point.y} projects'
        },
        yAxis: {
            title: { text: '% of Projects' },
            reversedStacks: false
        },
        xAxis: {
            categories: ['Finished Libraries', 'In-house Library Prep']
        },
        plotOptions: {
            series: {
                stacking: 'percent',
                dataLabels: {
                    enabled: true,
                    formatter: function(){
                        if(this.percentage > 60){
                            return this.percentage.toFixed(0) + '%';
                        }
                    }
                }
            }
        },
        series: pdata
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
        credits: { enabled: false },
        tooltip: {
            headerFormat: '',
            pointFormat: '<span style="color:{point.color}; font-weight:bold;">{point.name}</span>: {point.y} projects'
        },
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
    var total_count = 0;
    for(j=0; j<skeys.length; j++){
        var swdata = Array();
        for(i=0; i<num_weeks; i++){
            thisdata = data['bp_seq_per_week'][weeks[i]][skeys[j]];
            swdata.push(thisdata == undefined ? 0 : thisdata);
            total_count += thisdata == undefined ? 0 : thisdata;
        }
        sdata.push({
            name: skeys[j],
            data: swdata
        });
    }
    // Subtitle text
    var bp_per_day = total_count / (num_weeks * 7);
    var minutes_per_genome = 3236336281 / (bp_per_day / (24*60));
    var subtitle_text = 'Average for past '+num_weeks+' weeks: '+parseInt(bp_per_day/1000000000)+' Gbp per day <br>(1 Human genome equivalent every '+minutes_per_genome.toFixed(2)+' minutes)';
    
    $('#throughput_plot').highcharts({
        chart: {
            plotBackgroundColor: null,
            height: plot_height,
            type: 'area'
        },
        title: {
            text: 'Sequencing Throughput',
            style: { 'font-size': '24px' }
        },
        subtitle: {
            text: subtitle_text
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
            title: { text: 'Base Pairs' },
            labels: {
                formatter: function () {
                    return this.value.toExponential();
                }
            }
        },
        credits: { enabled: false },
        tooltip: {
            shared: true,
            useHTML: true,
            formatter: function(){
                tt = '<strong>Week of '+weeks[this.x]+'</strong><br><table>';
                for(i=0; i<this.points.length; i++){
                    tt += '<tr><td style="padding-right: 15px;"><span style="color:'+this.points[i].color+';">'
                    tt += this.points[i].series.name+'</span>:</td><td class="text-right">'
                    tt += parseInt(this.points[i].y/1000000000)+' Gbp</td></tr>';
                }
                tt += '<tr style="border-top: 1px solid #333;"><td><strong>Total:</strong></td>';
                tt += '<td>'+parseInt(this.points[0].total/1000000000)+' Gbp</td></tr></table>';
                return tt;
            }
        },
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
            y: 80,
            x: 90,
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

