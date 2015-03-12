function addAxesAndLegend (svg, xAxis, yAxis, margin, chartWidth, chartHeight) {
  var legendWidth  = 200,
      legendHeight = 180;

  // clipping to make sure nothing appears behind legend
  svg.append('clipPath')
    .attr('id', 'axes-clip')
    .append('polygon')
      .attr('points', (-margin.left)                 + ',' + (-margin.top)                 + ' ' +
                      (chartWidth -  1)              + ',' + (-margin.top)                 + ' ' +
                      (chartWidth -  1)              + ',' + legendHeight                  + ' ' +
                      (chartWidth + margin.right)    + ',' + legendHeight                  + ' ' +
                      (chartWidth + margin.right)    + ',' + (chartHeight + margin.bottom) + ' ' +
                      (-margin.left)                 + ',' + (chartHeight + margin.bottom));

  var axes = svg.append('g')
    .attr('clip-path', 'url(#axes-clip)');

  axes.append('g')
    .attr('class', 'x axis')
    .call(xAxis)
    .attr('transform', 'translate(0,' + chartHeight + ')')
    .append('text')
      .attr('x', chartWidth - 60)
      .attr('dy', '-.71em')
      .text('Iteration');
    ;

  axes.append('g')
    .attr('class', 'y axis')
    .call(yAxis)
    .append('text')
      .attr('transform', 'rotate(-90)')
      .attr('y', 6)
      .attr('dy', '.71em')
      .style('text-anchor', 'end')
      .text('Accuracy (%)');

  var legend = svg.append('g')
    .attr('class', 'legend')
    .attr('transform', 'translate(' + (chartWidth - legendWidth) + ', 0)');

  var legendPosition = legendWidth + 10;

  legend.append('rect')
    .attr('class', 'legend-bg')
    .attr('width',  legendWidth)
    .attr('height', legendHeight)
    .attr('x', legendPosition);

  legend.append('text')
    .attr('class', 'section')
    .attr('x', legendPosition + 10)
    .attr('y', 25)
    .text('Control Group Validation:');
    
  legend.append('path')
    .attr('class', 'controlGroupAccuracy-line')
    .attr('d', 'M' + (legendPosition + 10) + ',45L' + (legendPosition + 60) + ',45');
    
  legend.append('text')
    .attr('x', legendPosition + 75)
    .attr('y', 50)
    .text('Accuracy');

  legend.append('text')
    .attr('class', 'section')
    .attr('x', legendPosition + 10)
    .attr('y', 80)
    .text('5-Fold Validation:');

  legend.append('path')
    .attr('class', 'mean-line')
    .attr('d', 'M' + (legendPosition + 10) + ',100L' + (legendPosition + 60) + ',100');

  legend.append('text')
    .attr('x', legendPosition + 75)
    .attr('y', 105)
    .text('Mean Accuracy');

  legend.append('rect')
    .attr('class', 'upper')
    .attr('width',  50)
    .attr('height', 20)
    .attr('x', legendPosition + 10)
    .attr('y', 120);

  legend.append('text')
    .attr('x', legendPosition + 75)
    .attr('y', 135)
    .text('Upper Accuracy');

  legend.append('rect')
    .attr('class', 'lower')
    .attr('width',  50)
    .attr('height', 20)
    .attr('x', legendPosition + 10)
    .attr('y', 150);

  legend.append('text')
    .attr('x', legendPosition + 75)
    .attr('y', 165)
    .text('Lower Accuracy');
}

function drawPaths (svg, accuracyData, chartWidth, chartHeight, x, y) {
  
  var upperOuterArea = d3.svg.area()
    .interpolate('cardinal')
    .x (function (d) { return x(d.iteration) || 1; })
    .y0(function (d) { return y(d.upper); })
    .y1(function (d) { return y(d.mean); });

  var meanLine = d3.svg.line()
    .interpolate('cardinal')
    .x(function (d) { return x(d.iteration); })
    .y(function (d) { return y(d.mean); });

  var lowerInnerArea = d3.svg.area()
    .interpolate('cardinal')
    .x (function (d) { return x(d.iteration) || 1; })
    .y0(function (d) { return y(d.mean); })
    .y1(function (d) { return y(d.lower); });

  var controlGroupAccuracyLine = d3.svg.line()
    .interpolate('cardinal')
    .x(function (d) { return x(d.iteration); })
    .y(function (d) { return y(d.controlGroupAccuracy); });

  svg.datum(accuracyData);

  svg.append('path')
    .attr('class', 'area upper')
    .attr('d', upperOuterArea)
    .attr('clip-path', 'url(#chart-clip)');

  svg.append('path')
    .attr('class', 'area lower')
    .attr('d', lowerInnerArea)
    .attr('clip-path', 'url(#chart-clip)');

  svg.append('path')
    .attr('class', 'mean-line')
    .attr('d', meanLine)
    .attr('clip-path', 'url(#chart-clip)');
    
  svg.append('path')
    .attr('class', 'controlGroupAccuracy-line')
    .attr('d', controlGroupAccuracyLine)
    .attr('clip-path', 'url(#chart-clip)');
    
}

function tooltips(svg, accuracyData, chartWidth, chartHeight, x, y){
  var tooltipElement = []
  var mouseHoverLine = []
    
  var mouseLine = svg.append('rect')
    .attr('class', 'mouseLine')
    .attr('width',  1)
    .attr('height',  chartHeight)
    .style('display', 'none')
    .style('pointer-events', 'none');
  mouseHoverLine.push(mouseLine);
    
  var mouseUpperPoint = svg.append('circle')
    .attr('class', 'mouseUpperPoint')
    .attr('r', 4)
    .style('display', 'none')
    .style('pointer-events', 'none');
  mouseHoverLine.push(mouseUpperPoint);
    
  var mouseLowerPoint = svg.append('circle')
    .attr('class', 'mouseLowerPoint')
    .attr('r', 4)
    .style('display', 'none')
    .style('pointer-events', 'none');
  mouseHoverLine.push(mouseLowerPoint);
    
  var mouseMeanPoint = svg.append('circle')
    .attr('class', 'mouseMeanPoint')
    .attr('r', 5)
    .style('display', 'none')
    .style('pointer-events', 'none');
  mouseHoverLine.push(mouseMeanPoint);
    
  var mouseControlGroupAccuracyPoint = svg.append('circle')
    .attr('class', 'mouseControlGroupAccuracyPoint')
    .attr('r', 5)
    .style('display', 'none')
    .style('pointer-events', 'none');
  mouseHoverLine.push(mouseControlGroupAccuracyPoint);
    
  var mouseTooltipBox = svg.append('rect')
    .attr('class', 'tooltipbox')
    .attr('width',  220)
    .attr('height', 130)
    .attr('x', 12)
    .attr('y', 20)
    .style('display', 'none')
    .style('pointer-events', 'none');
  tooltipElement.push(mouseTooltipBox);
  
  var mouseTooltipIter = svg.append('text')
          .attr('class', 'tooltipText')
          .attr('x', 17)
          .attr('y', 35)
          .style('display', 'none')
          .style('pointer-events', 'none');
  tooltipElement.push(mouseTooltipIter);
          
  var mouseTooltipCGPSize = svg.append('text')
          .attr('class', 'tooltipText')
          .attr('x', 17)
          .attr('y', 50)
          .style('display', 'none')
          .style('pointer-events', 'none');
  tooltipElement.push(mouseTooltipCGPSize);
          
  var mouseTooltipCGPAcc = svg.append('text')
          .attr('class', 'tooltipText')
          .attr('x', 17)
          .attr('y', 65)
          .style('display', 'none')
          .style('pointer-events', 'none');
  tooltipElement.push(mouseTooltipCGPAcc);
  
  var mouseTooltipAcc = svg.append('text')
          .attr('class', 'tooltipText')
          .attr('x', 17)
          .attr('y', 80)
          .style('display', 'none')
          .style('pointer-events', 'none');
  tooltipElement.push(mouseTooltipAcc);
          
  var mouseTooltipDev = svg.append('text')
          .attr('class', 'tooltipText')
          .attr('x', 17)
          .attr('y', 95)
          .style('display', 'none')
          .style('pointer-events', 'none');
  tooltipElement.push(mouseTooltipDev);
          
  var mouseTooltipSam = svg.append('text')
          .attr('class', 'tooltipText')
          .attr('x', 17)
          .attr('y', 110)
          .style('display', 'none')
          .style('pointer-events', 'none');
  tooltipElement.push(mouseTooltipSam);
          
  var mouseTooltipPay = svg.append('text')
          .attr('class', 'tooltipText')
          .attr('x', 17)
          .attr('y', 125)
          .style('display', 'none')
          .style('pointer-events', 'none');
  tooltipElement.push(mouseTooltipPay);
          
  var mouseTooltipTime = svg.append('text')
          .attr('class', 'tooltipText')
          .attr('x', 17)
          .attr('y', 140)
          .style('display', 'none')
          .style('pointer-events', 'none');
  tooltipElement.push(mouseTooltipTime);
  
  var insufficientAlert = svg.append('text')
          .attr('class', 'tooltipText-danger')
          .attr('x', 17)
          .attr('y', 155)
          .style('display', 'none')
          .style('pointer-events', 'none')
          .text('*Unsure evaluation (insufficient samples)');
  tooltipElement.push(insufficientAlert);
  
  var bisect = d3.bisector(function(accuracyData) {
    return accuracyData.iteration;
  }).left;
  
  if(accuracyData.length != 1){
    svg.append("rect")
      .attr("class", "overlay")
      .attr("width", chartWidth)
      .attr("height", chartHeight)
      /*.on("mouseover", function() {
        jQuery.each(mouseHoverLine, function (i, val){val.style("display", null);});
        jQuery.each(tooltipElement, function (i, val){val.style("display", null);});
      })*/
      .on("mouseout", function() { 
        jQuery.each(mouseHoverLine, function (i, val){val.style("display", "none");});
        jQuery.each(tooltipElement, function (i, val){val.style("display", "none");});
       })
      .on("mousemove", function() {
        var x0 = x.invert(d3.mouse(this)[0]),
          i = bisect(accuracyData, x0, 1),
          d0 = accuracyData[i - 1],
          d1 = accuracyData[i],
          d = x0 - d0.iteration > d1.iteration - x0 ? d1 : d0;
        if(d.iteration!=0){
          jQuery.each(mouseHoverLine, function (i, val){val.style("display", null);});
          jQuery.each(tooltipElement, function (i, val){val.style("display", null);});
          mouseLine.attr("transform", "translate(" + x(d.iteration) + "," + 0 + ")"); 
          mouseUpperPoint.attr("transform", "translate(" + x(d.iteration) + "," + y(d.upper) + ")");
          mouseLowerPoint.attr("transform", "translate(" + x(d.iteration) + "," + y(d.lower) + ")");
          mouseMeanPoint.attr("transform", "translate(" + x(d.iteration) + "," + y(d.mean) + ")");
          mouseControlGroupAccuracyPoint.attr("transform", "translate(" + x(d.iteration) + "," + y(d.controlGroupAccuracy) + ")");
          
          jQuery.each(tooltipElement, function (i, val){
            _y = d.controlGroupAccuracy > d.mean? d.controlGroupAccuracy : d.mean;
            val.attr("transform", "translate(" + x(d.iteration) + "," + y(_y) + ")");
          });
          
          mouseTooltipIter.text('Iteration: ' + d.iteration);
          mouseTooltipCGPSize.text('Control Group (CG) Size: ' + d.controlGroupSize);
          mouseTooltipCGPAcc.text('CG Validation Accuracy: ' + d.controlGroupAccuracy + '%');
          mouseTooltipAcc.text('5-fold Validation Accuracy: ' + d.mean + '%');
          mouseTooltipDev.text('5-fold Validation Deviation (+/-): ' + d.deviation + '%');
          mouseTooltipSam.text('Labeled sample: ' + d.sampleAmount);
          mouseTooltipPay.text('Payment: USD$' + d.payment);
          var formattedDatTime = d3.time.format('%Y/%m/%d %X');
          mouseTooltipTime.text('(At ' + formattedDatTime(d.time) + ')');
          
          var inIZ = x(d.iteration) < insufficientZoneWidth;
          insufficientAlert.style("display", inIZ?null:'none');
          mouseTooltipBox.attr('height', inIZ?140:130);
          mouseTooltipBox.attr('width', inIZ?240:220);
          mouseTooltipCGPSize.attr('class', inIZ?'tooltipText-warning':'tooltipText');
          mouseTooltipCGPAcc.attr('class', inIZ?'tooltipText-warning':'tooltipText');
          mouseTooltipAcc.attr('class', inIZ?'tooltipText-warning':'tooltipText');
          mouseTooltipDev.attr('class', inIZ?'tooltipText-warning':'tooltipText');
          mouseTooltipSam.attr('class', inIZ?'tooltipText-warning':'tooltipText');
        }
      });
  }
}

var insufficientZoneWidth = 0;

function drawInsufficientZone(svg, accuracyData, chartWidth, chartHeight){
  if(accuracyData.length == 1)
    return;

  var i = 0;
  for(i = 0; i < accuracyData.length; i++){
    if(accuracyData[i].sampleAmount > 80)
      break;
    else if(accuracyData[i].controlGroupSize > 0){
      i++;
      break;
    }
  }
  
  if(i == 1){
    return;
  }
  
  var zone = svg.append('g')
    .attr('class', 'legend')
    .attr('transform', 'translate(0,0)');
  
  insufficientZoneWidth = chartWidth*i/(accuracyData.length-1);
  var insufficientZone = zone.append('rect')
  .attr('id', 'insufficientZone')
  .attr('width', insufficientZoneWidth)
  .attr('height', chartHeight)
  .attr('fill', 'url(#insufficientZoneColor)')
  .attr('clip-path', 'url(#chart-clip)')
  .style('pointer-events', 'none');
  
  //Vertical indicator
  /*var zoneEdge = chartWidth*(i-1)/(accuracyData.length-1);
  zone.append('path')
    .attr('class', 'zone-edge')
    .attr('d', 'M' + (zoneEdge) + ',0L' + (zoneEdge) + ',' + chartHeight);
  
  zone.append('text')
    .attr('class', 'section')
    .text('↓ Insufficient Sample Zone ↓')
    .style('font-size', '' + chartHeight/15 + 'px')
    .attr('transform', 'rotate(90)')
    .attr('x', 0)
    .attr('y', 0 - zoneWidth*0.7);
  */
  
  //Separated lines
  /*
  zone.append('text')
    .attr('class', 'section')
    .text('Insufficient')
    .style('font-size', '' + zoneWidth/20 + 'px')
    .attr('x', 30)
    .attr('y', chartHeight * 0.3)
    .attr('clip-path', 'url(#chart-clip)');
  
  zone.append('text')
    .attr('class', 'section')
    .text('Samples')
    .style('font-size', '' + zoneWidth/20 + 'px')
    .attr('x', 30)
    .attr('y', chartHeight * 0.3 + 30)
    .attr('clip-path', 'url(#chart-clip)');
    
  zone.append('text')
    .attr('class', 'section')
    .text('Zone')
    .style('font-size', '' + zoneWidth/20 + 'px')
    .attr('x', 30)
    .attr('y', chartHeight * 0.3 + 60)
    .attr('clip-path', 'url(#chart-clip)');*/
    
}

function addMarker (marker, svg, chartHeight, x) {
  var radius = 25,
      xPos = x(marker.iteration) - radius,
      yPosStart = chartHeight - radius - 3,
      yPosEnd = 0 - radius*2 - 3; //radius - 3;

  var markerG = svg.append('g')
    .attr('class', 'marker ' + marker.type.toLowerCase())
    .attr('transform', 'translate(' + xPos + ', ' + yPosStart + ')')
    .attr('opacity', 0);

  markerG.transition()
    .duration(1000)
    .attr('transform', 'translate(' + xPos + ', ' + yPosEnd + ')')
    .attr('opacity', 1);

  markerG.append('path')
    .attr('d', 'M' + radius + ',' + (chartHeight-yPosStart) + 'L' + radius + ',' + (chartHeight-yPosStart))
    .transition()
      .duration(1000)
      .attr('d', 'M' + radius + ',' + (chartHeight-yPosEnd) + 'L' + radius + ',' + (radius*2));

  markerG.append('circle')
    .attr('class', 'marker-bg')
    .attr('cx', radius)
    .attr('cy', radius)
    .attr('r', radius)
    .style('pointer-events', 'none');;

  markerG.append('text')
    .attr('x', radius)
    .attr('y', radius*1.2)
    .text(marker.word)
    .style('pointer-events', 'none');;
}

function startTransitions (svg, chartWidth, chartHeight, chartClip, markers, x) {
  //Display chart from left to right
  chartClip.transition()
    .duration(2500)
    .attr('width', chartWidth);
  
  //Display execution markers
  markers.forEach(function (marker, i) {
    setTimeout(function () {
      addMarker(marker, svg, chartHeight, x);
    }, (2500/(markers.length+1))*i);
  });
  
}

function makeChart () {
  var svgWidth  = $('#accuracyChart').width()+120,
      svgHeight = $(window).height()-270 > 500?500: $(window).height()-270,
      margin = { top: 60, right: 240, bottom: 40, left: 40 },
      chartWidth  = svgWidth  - margin.left - margin.right,
      chartHeight = svgHeight - margin.top  - margin.bottom;
  $("#accuracyChart").empty();
  var x = d3.scale.linear().range([0, chartWidth])
            .domain(d3.extent(accuracyData, function (d) { return d.iteration; })),
      y = d3.scale.linear().range([chartHeight, 0])
            .domain([d3.min(accuracyData, function (d) { return d.upper; })*3/4, 100]);

  var xAxis = d3.svg.axis().tickFormat(d3.format("d")).scale(x).orient('bottom')
                .innerTickSize(-chartHeight).outerTickSize(0).tickPadding(10),
      yAxis = d3.svg.axis().scale(y).orient('left')
                .innerTickSize(-chartWidth).outerTickSize(0).tickPadding(10);

  var svg = d3.select('#accuracyChart').append('svg')
    .attr('width',  svgWidth)
    .attr('height', svgHeight)
    .append('g')
      .attr('transform', 'translate(' + margin.left + ',' + margin.top + ')');

  // clipping to start chart hidden and slide it in later
  var chartClip = svg.append('clipPath')
    .attr('id', 'chart-clip')
    .append('rect')
      .attr('width', 0)
      .attr('height', chartHeight);
  
  //Render Axes and legend
  addAxesAndLegend(svg, xAxis, yAxis, margin, chartWidth, chartHeight);
  
  //Render lines and areas
  drawPaths(svg, accuracyData, chartWidth, chartHeight, x, y);
  
  //Render tooltips and relative mouse event
  tooltips(svg, accuracyData, chartWidth, chartHeight, x, y);
  
  //Render insufficient zone
  drawInsufficientZone(svg, accuracyData, chartWidth, chartHeight);
  
  //Display animation
  startTransitions(svg, chartWidth, chartHeight, chartClip, markers, x);
}

var accuracyData;
var markers;
var parseDateTime = d3.time.format('%a, %d %b %Y %X GMT').parse;
function getAccuracyData(){
  d3.json('_getAccuracyData', function (error, rawData) {
    if (error) {
      console.error(error);
      return;
    }

    accuracyData = rawData.data.map(function (d) {
      return {
        iteration:  d.iteration,
        deviation: parseInt(d.deviation * 100), 
        lower: parseInt((d.kFoldAccuracy - d.deviation) * 100 < 0? 0: (d.kFoldAccuracy - d.deviation) * 100),
        mean: parseInt(d.kFoldAccuracy * 100),
        upper: parseInt((d.kFoldAccuracy + d.deviation) *100 > 100? 100: (d.kFoldAccuracy + d.deviation) *100),
        controlGroupAccuracy: parseInt(d.controlGroupAccuracy * 100),
        controlGroupSize: parseInt(d.controlGroupSize),
        sampleAmount: parseInt(d.sampleAmount),
        payment: d.payment,
        time: parseDateTime(d.time)
      };
    });

    d3.json('_getExecutionMarkers', function (error, markerData) {
      if (error) {
        console.error(error);
        return;
      }

      markers = markerData.marker.map(function (marker) {
        var displayWord;
        if(marker.type == 'start'){ displayWord = 'Start' }
        else if(marker.type == 'finish'){ displayWord = 'Finish' }
        else if(marker.type == 'finishWithError'){ displayWord = 'End' }
        else if(marker.type == 'terminatedAsRequests'){ displayWord = 'Stop' }
        return {
          iteration: marker.iteration,
          type: marker.type,
          word: displayWord,
        };
      });

      makeChart();
    });
  });
}
