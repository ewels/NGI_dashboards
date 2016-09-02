
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
        var cats = Object.keys(ydata).sort(function(a,b){return ydata[a]-ydata[b]}).reverse();
        var sorted_ydata = Array();
        var num_projects_cats = Array();
        for(j=0; j<cats.length; j++){
            if(data['key_names'][cats[j]] == undefined){
                num_projects_cats.push(cats[j]);
            } else {
                num_projects_cats.push(data['key_names'][cats[j]]);
            }
            sorted_ydata.push(ydata[cats[j]]);
        }
        var num_projects_data = [{ name: years[0], data: sorted_ydata }];
        $('#num_projects_heading').text('# Projects in '+years[0]);
        make_bar_plot('#num_projects_plot', num_projects_cats, num_projects_data);
        
        // # Samples plot
        var years = Object.keys(data['num_samples']).sort().reverse();
        var ydata = data['num_samples'][years[0]];
        var cats = Object.keys(ydata).sort(function(a,b){return ydata[a]-ydata[b]}).reverse();
        var sorted_ydata = Array();
        var num_samples_cats = Array();
        for(j=0; j<cats.length; j++){
            if(data['key_names'][cats[j]] == undefined){
                num_samples_cats.push(cats[j]);
            } else {
                num_samples_cats.push(data['key_names'][cats[j]]);
            }
            sorted_ydata.push(ydata[cats[j]]);
        }
        var num_samples_data = [{ name: years[0], data: sorted_ydata }];
        console.log(num_samples_cats);
        console.log(num_samples_data);
        $('#num_samples_heading').text('# Samples in '+years[0]);
        make_bar_plot('#num_samples_plot', num_samples_cats, num_samples_data);
        
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
                height: 300,
                backgroundColor:'rgba(255, 255, 255, 0.1)'
            },
            title: {
                text: null
            },
            tooltip: { enabled: false },
            credits: { enabled: false },
            xAxis: {
                categories: categories
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

