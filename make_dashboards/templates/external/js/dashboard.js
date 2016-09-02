
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
                height: 300,
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
            height: 300,
        },
        title: {
            text: 'Delivery Times in '+years[0],
            style: { 'font-size': '24px' }
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
                size: '150%',
                center: ['50%', '75%']
            }
        },
        legend: {
            enabled: true,
            floating: true
        },
        series: [{
            type: 'pie',
            name: 'Delivery Times',
            innerSize: '50%',
            data: pdata
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
    
    var updated = moment($('#time_created').data('original'));
    $('#report_age').text( moment().from(updated, true) );
    setTimeout(updateClock, 1000);
}

