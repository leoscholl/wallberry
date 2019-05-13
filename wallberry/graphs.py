from datetime import timedelta, datetime, timezone
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib import rcParams as defaults
from matplotlib.patches import Rectangle
import io


defaults.update({'font.size':16,
    'font.family':'sans-serif',
    'font.sans-serif':'Verdana',
    'axes.linewidth':2,
    'lines.linewidth':3})

def history_graph(log, width, unit):
    dpi = 100
    figsize = (width / dpi, 0.3 * width / dpi)
    fg = '#cccccc'
    bg = '#000000'
    fig = Figure(figsize=figsize, dpi=dpi, facecolor=bg, frameon=False)

    taxis = fig.add_axes((0.08, 0.1, 0.68, 0.9), facecolor=bg)
    lines = []
    for sensor in log:
        lines.append(taxis.plot(log[sensor]['time'], log[sensor]['value']))
    taxis.set_ylabel('Temp (%s)' % unit, color=fg)
    taxis.xaxis.set_tick_params(color=fg, labelcolor=fg)
    taxis.yaxis.set_tick_params(color=fg, labelcolor=fg)

    formatter = taxis.xaxis.get_major_formatter()
    formatter.scaled[1./24] = '%-I%P'
    formatter.scaled[1.0] = '%e'
    formatter.scaled[30.] = '%b'
    formatter.scaled[365.] = '%Y'
    #taxis.xaxis.set_major_formatter(mdates.DateFormatter('%-I%P'))
    fig.legend(labels=log.keys())  

    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    return output

def hourly_graph(forecast, start, hours, width, unit):
    offset = timedelta(hours=forecast.offset())
    end = start + timedelta(hours=hours)
    time = []
    temp = []
    precip = []
    hour = 0
    hf = forecast.hourly().data[hour]
    while hf.time + offset < end:
        time.append(hf.time + offset)
        temp.append(hf.temperature)
        precip.append(hf.precipProbability*100)
        hour += 1
        hf = forecast.hourly().data[hour]

    dpi = 100
    figsize = (width / dpi, 0.3 * width / dpi)
    fg = '#cccccc'
    bg = '#000000'
    fig = Figure(figsize=figsize, dpi=dpi, facecolor=bg, frameon=False)

    # Temperature
    taxis = fig.add_axes((0.08, 0.1, 0.84, 0.8), facecolor=bg)
    taxis.plot(time, temp, color=fg)
    taxis.set_ylabel('Temp (%s)' % unit, color=fg)
    taxis.xaxis.set_tick_params(color=fg, labelcolor=fg)
    taxis.yaxis.set_tick_params(color=fg, labelcolor=fg)

    # Precipitation
    paxis = taxis.twinx()
    fg2 = '#4082f2'
    paxis.plot(time, precip, color=fg2)
    paxis.set_ylabel('Chance (%)', color=fg2)
    paxis.xaxis.set_tick_params(color=fg2, labelcolor=fg2)
    paxis.yaxis.set_tick_params(color=fg2, labelcolor=fg2)

    paxis.spines['bottom'].set_color(fg)
    paxis.spines['left'].set_color(fg)
    paxis.spines['right'].set_color(fg)
    paxis.spines['top'].set_visible(False)

    paxis.xaxis.set_major_formatter(mdates.DateFormatter('%-I%P'))
    paxis.set_xlim([start.replace(minute=0), end.replace(minute=0)])

    xticks = [start.replace(minute=0) + timedelta(hours=x) \
        for x in range(0, hours + 1, 2)]
    paxis.set_xticks(xticks)

    yticks = range(0, 101, 25)
    paxis.set_yticks(yticks)

    for ymaj in taxis.yaxis.get_majorticklocs():
        taxis.axhline(y=ymaj, ls='-', color='#555555', lw=0.5)

    # Annotate highs and lows
    high = max(temp[1:-1])
    tHigh = time[temp.index(high)]
    if tHigh > start + timedelta(hours=1):
        taxis.annotate('%d%s' % (high, unit), xy=(tHigh, high),
            xytext=(0,4), textcoords='offset points', color=fg)
    low = min(temp[1:-1])
    tLow = time[temp.index(low)]
    if tLow > start + timedelta(hours=1):
        taxis.annotate('%d%s' % (low, unit), xy=(tLow, low),
            xytext=(0,4), textcoords='offset points', color=fg)
    prec = max(precip[1:-1])
    tPrec = time[precip.index(prec)]
    paxis.annotate('%d%%' % (prec), xy=(tPrec, prec),
        xytext=(0,4), textcoords='offset points', color=fg2)

    # Sunset-sunrise rectangles
    day = 0
    df = forecast.daily().data[day]
    while df.time + offset < end:
        sr = mdates.date2num(df.sunriseTime + offset)
        ss = mdates.date2num(df.sunsetTime + offset)
        width = ss - sr
        ymin, ymax = taxis.get_ylim()
        height = ymax - ymin
        rect = Rectangle((sr, ymin), width, height, color='#ffff00', alpha=0.1)
        taxis.add_patch(rect)
        day += 1
        df = forecast.daily().data[day]

    canvas = FigureCanvas(fig)
    output = io.BytesIO()
    canvas.print_png(output)
    return output

