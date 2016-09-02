
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
        
        // Projects plot
        var num_years = 2;
        var p_cutoff = 5;
        var years = Object.keys(data['num_projects']).sort().reverse();
        num_projects_cats = Array();
        num_projects_data = Array();
        // Find the total counts for all years
        var dtotal = Array();
        for(var i=0; i<num_years; i++){
            for(k in data['num_projects'][years[i]]){
                if(dtotal[k] == undefined){
                    dtotal[k] = data['num_projects'][years[i]][k];
                } else {
                    dtotal[k] += data['num_projects'][years[i]][k];
                }
            }
        }
        var num_projects_cats = Object.keys(dtotal).sort(function(a,b){return dtotal[a]-dtotal[b]}).reverse();
        // Get the data
        for(var i=(num_years-1); i>=0; i--){
            var year = years[i];
            var yeardata = Array();
            for(j=0; j<num_projects_cats.length; j++){
                if(dtotal[num_projects_cats[j]] >= p_cutoff){
                    if(data['num_projects'][year][num_projects_cats[j]] == undefined){
                        yeardata.push(0);
                    } else {
                        yeardata.push(data['num_projects'][year][num_projects_cats[j]]);
                    }
                }
            }
            num_projects_data.push({
                'name': year,
                'data': yeardata,
                'dataLabels': {
                    'enabled': i == 0
                }
            });
        }
        make_bar_plot('#num_projects_plot', num_projects_cats, num_projects_data);
        
    } catch(err){
        $('.main-page').html('<div class="alert alert-danger text-center" style="margin: 100px 50px;"><p><strong>Error loading dashboard data</strong></p></div><pre style="margin: 100px 50px;"><code>'+err+'</code></pre>');
        console.log(err);
        // Try reloading in a few minutes
        setTimeout(function(){ location.reload(); }, 300000); // 5 minutes
    }
    
});


// Make a bar plot
function make_bar_plot(target, categories, data, title){
    try {
        if(target === undefined){ throw 'Target missing'; }
        if(categories === undefined){ throw 'Categories missing'; }
        $(target).highcharts({
            chart: {
                type: 'bar',
                height: 500,
                backgroundColor:'rgba(255, 255, 255, 0.1)'
            },
            tooltip: { enabled: false },
            credits: { enabled: false },
            xAxis: {
                categories: categories
            },
            yAxis: {
                min: 0,
            },
            legend: {
                reversed: true,
                layout: 'vertical',
                align: 'right',
                verticalAlign: 'bottom',
                x: -20,
                y: -60,
                floating: true,
                borderWidth: 1,
                backgroundColor: ((Highcharts.theme && Highcharts.theme.legendBackgroundColor) || '#FFFFFF'),
                shadow: true
            },
            plotOptions: {
                bar: {
                    borderWidth: 0
                }
            },
            series: data
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

