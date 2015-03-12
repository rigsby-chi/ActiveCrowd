function getPieChartData(url, chartInfo, displaySelector){
  d3.json(url, function (error, tempHITData) {
    if (error) {
      console.error(error);
      return;
    }
    count = 0;
    retievedData = tempHITData.data.map(function (d) {
      count ++;
      console.log(d.description);
      console.log(count-1);
      return {
        label: d.description,
        rate: parseFloat(d.rate),
        order: count-1
      }
    });
    colorGenerator(retievedData.length);
    if(retievedData.length == 0)
      chartInfo = NoRecord
    drawPieChart(retievedData, chartInfo, displaySelector);
  });
}

var DURATION = 1500;
var DELAY    = 500;

var color = [];
var stokeColor = [];

function colorGenerator(number){
  color = [];
  stokeColor = [];
  for(var i = 0; i < number; i++){
    color.push('hsl(' + parseInt((210+i*360/number)%360) + ',100%,65%)');
    stokeColor.push('hsl(' + parseInt((210+i*360/number)%360) + ',100%,35%)');
  }
}

function drawChartCenter(chartInfo, pie, radius) {
  var centerContainer = pie.append( 'g' )
                            .attr( 'class', 'pieChart--center' );
  
  centerContainer.append( 'circle' )
    .attr( 'class', 'pieChart--center--outerCircle' )
    .attr( 'r', 0 )
    .attr( 'filter', 'url(#pieChartDropShadow)' )
    .transition()
    .duration( DURATION )
    .delay( DELAY )
    .attr( 'r', radius * 0.63 );
  
  centerContainer.append( 'circle' )
    .attr( 'id', 'pieChart-clippy' )
    .attr( 'class', 'pieChart--center--innerCircle' )
    .attr( 'r', 0 )
    .transition()
    .delay( DELAY )
    .duration( DURATION )
    .attr( 'r', radius * 0.63 - 4 )
    .attr( 'fill', '#fff' );
  
  centerContainer.append( 'text' )
    .text('')
    .style("text-anchor", "middle")
    .style("font-size", '' + radius * 0.15 + 'px')
    .attr("dy", '-' + radius * 0.15 + 'px')
    .transition()
    .delay( DELAY + DURATION )
    .duration( DURATION )
    .text(chartInfo.header);
    
  centerContainer.append( 'text' )
    .text(chartInfo.des)
    .style("text-anchor", "middle");
}

function autoNewLine(caller, width, sizeRadio){
  caller.each(function() {
    var text = d3.select(this),
        words = text.text().split(/\s+/).reverse(),
        word,
        line = [],
        lineNumber = 0,
        lineHeight = 1.1, // ems
        tspan = text.text(null).append("tspan").style("font-size", '' + width/sizeRadio + 'px');
        
    while (word = words.pop()) {
      line.push(word);
      tspan.text(line.join(" "));
      if (tspan.node().getComputedTextLength() > width) {
        line.pop();
        tspan.text('')
          .attr('x', 0)
          .attr('dy', '' + width/(sizeRadio-2))
          .attr('class', 'pieChart--detail--textContainer')
          .transition()
          .delay( DELAY + DURATION )
          .duration( DURATION )
          .text(line.join(" "));
        line = [word];
        tspan = text.append("tspan").style("font-size", '' + width/sizeRadio + 'px').text(word);
      }
    }
    temp = tspan.text();
    tspan.text('')
      .attr('x', 0)
      .attr('dy', '' + width/(sizeRadio-2))
      .attr('class', 'pieChart--detail--textContainer')
      .transition()
      .delay( DELAY + DURATION )
      .duration( DURATION )
      .text(temp);
  });
}

function drawPieChart(retievedData, chartInfo, elementId){
  $(elementId).empty();
  var width = $(elementId).width();
  var height = $(window).height()-120 > 700?700: $(window).height()-120;

  var svg = d3.select(elementId)
	  .append("svg")
	  .attr( 'width', width )
    .attr( 'height', height )
	  .append("g");

  var pieLayer = svg.append("g")
	  .attr("class", "slices")
	  .attr('transform', 'translate(' + (width/2+10) + ',' + height/2 + ')');
  var labelsLayer = svg.append("g")
	  .attr("class", "labels")
	  .attr('transform', 'translate(' + (width/2+10) + ',' + height/2 + ')');
  var linesLayer = svg.append("g")
	  .attr("class", "lines")
	  .attr('transform', 'translate(' + (width/2+10) + ',' + height/2 + ')');

	var radius = Math.min(width/4, height/2.5);

  var pie = d3.layout.pie()
	  .sort(null)
	  .value(function(d) {
		  return d.rate;
	  });

  var arc = d3.svg.arc()
	  .outerRadius(radius * 0.8)
	  .innerRadius( 0 );
	  
	var middleArc = d3.svg.arc()
	  .innerRadius(radius * 0.8)
	  .outerRadius(radius * 0.63);

  var outerArc = d3.svg.arc()
	  .innerRadius(radius*1)
	  .outerRadius(radius*1);

  var key = function(d){ return d.data.label; };

  change(retievedData);

  drawChartCenter(chartInfo, pieLayer, radius)
  
  svg.selectAll('.pieChart--center text').call(autoNewLine, radius, 12);

  function change(data) {

	  /* ------- PIE SLICES -------*/
	  var slice = svg.select(".slices").selectAll("path.slice")
		  .data(pie(data), key);

	  slice.enter()
		  .insert("path")
		  .style("fill", function(d) { return color[d.data.order]; })
		  .attr( 'filter', 'url(#pieChartInsetShadow)' )
		  .attr("class", "slice");

	  slice.each( function() {
        this._current = { startAngle: 0, endAngle: 0 }; 
       })
		  .transition()
		  .duration( DURATION )
		  .attrTween("d", function(d) {
			  this._current = this._current || d;
			  var interpolate = d3.interpolate(this._current, d);
			  this._current = interpolate(0);
			  return function(t) {
				  return arc(interpolate(t));
			  };
		  })

	  slice.exit()
		  .remove();
		  
		//Count the middle angle of an arc
		function midAngle(d){
		  return d.startAngle + (d.endAngle - d.startAngle)/2;
	  }

	  /* ------- Add Text label and description -------*/
    
	  var text = svg.select(".labels").selectAll("text")
		  .data(pie(data), key);

    infoWidth = radius * 0.75
        
	  text.enter()
	    .append('text')
      .attr('x', function(d) { 
        padding = midAngle(d) < Math.PI? 0 - radius*0.2:radius*0.2;
        return outerArc.centroid(d)[0] + padding; 
      })
      .attr('y', 0 - radius * 0.03 )
      .attr( 'font-size', '' + (radius * 0.1) + 'px')
      .attr('text-anchor', function(d) { return midAngle(d) < Math.PI?'end':'start'})
      .attr('transform', function(d) {
			  var pos = outerArc.centroid(d);
			  pos[0] = radius * (midAngle(d) < Math.PI ? 1 : -1);
			  return "translate("+ pos +")";
		  });
      
    text
      .transition()
      .delay( DURATION )
      .duration( DURATION )
      .tween( 'text', function( d ) {
        return function( t ) {
          a = parseFloat(this.textContent.split(' ')[0]) || 0;
          b = d.data.rate*100;
          this.textContent = '' + (a * (1 - t) + b * t).toFixed(1) + ' %';
        };
      })
      .each("start", drawDescription);
      
    text.exit()
		  .remove();
    
    var isDrawed = false;
    
    function drawDescription(d){
      if(!isDrawed){
        isDrawed = true;
        text.enter()
        .append( 'foreignObject' )
		    .attr( 'width', infoWidth ) 
        .attr( 'height', 100 )
        .attr( 'font-size', '' + (radius * 0.07) + 'px')
        .attr('x', function(d) { 
          padding = midAngle(d) < Math.PI? radius*0.05:0-radius*0.8;
          return outerArc.centroid(d)[0] + padding; 
        })
        .attr('y', function(d) { 
          return outerArc.centroid(d)[1] - radius * 0.05; 
        })
		    .html(function(d) {
			    return d.data.label;
		    }).attr('class', function(d) {
		      _class = 'pieChart--detail--textContainer pieChart--detail__';
          _class += midAngle(d) < Math.PI? 'right':'left';
          return _class;
        });
      }
    }
    
	  /* ------- Add PolyLines -------*/

	  var polyline = svg.select(".lines").selectAll("polyline")
		  .data(pie(data), key);
	
	  polyline.enter()
		  .append("polyline")
		  .style('stroke', function(d) { return stokeColor[d.data.order]; })
		  .style('stroke-width', '2')
		  .style('opacity', '0.3')
		  .style('fill', 'none');

	  polyline
	    .attr("points", function(d){
	      var start = outerArc.centroid(d);
	      start[0] = start[0] + (radius * 0.8 * (midAngle(d) < Math.PI ? 1 : -1));
			  return [start,start,start];
			})
	    .transition()
	    .delay( DURATION )
	    .duration( DURATION )
		  .attrTween("points", function(d){
			  return function(t) {
			    var start = outerArc.centroid(d);
			    start[0] = start[0] + (radius * 0.8 * (midAngle(d) < Math.PI ? 1 : -1));
			    var mid, end;
			    if(t <= 0.5){
			      mid = outerArc.centroid(d);
			      mid[0] = mid[0] + (radius * 0.8 * (midAngle(d) < Math.PI ? 1 : -1)) * (1 - t*2);
			      end = mid;
			    }
			    if(t >= 0.5){
			      mid = outerArc.centroid(d);
			      end = outerArc.centroid(d);
			      var _end = middleArc.centroid(d);
			      end[0] = (_end[0]-mid[0])*(t-0.5)*2 + mid[0];
			      end[1] = (_end[1]-mid[1])*(t-0.5)*2 + mid[1];
			    }
				  return [start, mid, end];
			  };			
		  });
	
	  polyline.exit()
		  .remove();
  };
}

var HITAnsweredRateInfo = {header: 'Answered Rate', des: 'This chart display the radio of HITs being answered or expired (the higher answer rate the better)'};

var HITPendingTimeInfo = {header: 'Pending Time', des: 'This chart display the time range of HITs between being created and being picked up by workers'};

var HITDurationRateInfo = {header: 'Duration Rate', des: 'This chart display the time workers spent on answering each HIT'};

var LabelDistributionInfo = {header: 'Label Distribution', des: 'This chart display the rate of labeled samples\' categories'};

var SamplePredictionInfo = {header: 'Sample Prediction', des: 'This chart display the prediction made by the latest model on all unlabeled samples'};

var OverallDistributionInfo = {header: 'Overall Distribution', des: 'This chart display the distribution of samples including actual labels and predicted labels'};

var NoRecord = {header: 'No Record', des: 'No record is found.'};

function getAndDrawPieChart(chartName){
  if(chartName == 'HITAnsweredRateChart')
    getPieChartData('_getHITAnsweredRate', HITAnsweredRateInfo, '#mturkHITCharts');
  else if(chartName == 'HITPendingTimeChart')
    getPieChartData('_getHITPendingTime', HITPendingTimeInfo, '#mturkHITCharts');
  else if(chartName == 'HITDurationRateChart')
    getPieChartData('_getHITDurationRate', HITDurationRateInfo, '#mturkHITCharts');
  else if(chartName == 'LabelDistributionChart')
    getPieChartData('_getLabelDistribution', LabelDistributionInfo, '#sampleCategoryCharts');
  else if(chartName == 'SamplePredictionChart')
    getPieChartData('_getSamplePrediction', SamplePredictionInfo, '#sampleCategoryCharts');
  else if(chartName == 'OverallDistributionChart')
    getPieChartData('_getOverallDistribution', OverallDistributionInfo, '#sampleCategoryCharts');
}
