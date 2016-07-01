/*
* Conditions Of Use 
* 
* This software was developed by employees of the National Institute of
* Standards and Technology (NIST), and others. 
* This software has been contributed to the public domain. 
* Pursuant to title 15 Untied States Code Section 105, works of NIST
* employees are not subject to copyright protection in the United States
* and are considered to be in the public domain. 
* As a result, a formal license is not needed to use this software.
* 
* This software is provided "AS IS."  
* NIST MAKES NO WARRANTY OF ANY KIND, EXPRESS, IMPLIED
* OR STATUTORY, INCLUDING, WITHOUT LIMITATION, THE IMPLIED WARRANTY OF
* MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, NON-INFRINGEMENT
* AND DATA ACCURACY.  NIST does not warrant or make any representations
* regarding the use of the software or the results thereof, including but
* not limited to the correctness, accuracy, reliability or usefulness of
* this software.
*/
package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.Defines;
import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.LoadEvent;
import com.google.gwt.event.dom.client.LoadHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.googlecode.gwt.charts.client.ChartLoader;
import com.googlecode.gwt.charts.client.ChartPackage;
import com.googlecode.gwt.charts.client.ColumnType;
import com.googlecode.gwt.charts.client.DataTable;
import com.googlecode.gwt.charts.client.corechart.ScatterChart;
import com.googlecode.gwt.charts.client.corechart.ScatterChartOptions;
import com.googlecode.gwt.charts.client.options.HAxis;
import com.googlecode.gwt.charts.client.options.Legend;
import com.googlecode.gwt.charts.client.options.LegendPosition;
import com.googlecode.gwt.charts.client.options.VAxis;
import com.reveregroup.gwt.imagepreloader.FitImage;

public class PowerVsTime implements SpectrumBrowserCallback<String> {

	private VerticalPanel vpanel;
	private SpectrumBrowser spectrumBrowser;
	private long freq;
	private int width;
	private int height;
	private String sensorId;
	private long selectionTime;
	private String url;
	private Image spectrumImage;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	public PowerVsTime(SpectrumBrowser mSpectrumBrowser,
			VerticalPanel powerVsTimePanel, String mSensorId,
			long mSelectionTime, long currentFreq, int canvasPixelWidth,
			int canvasPixelHeight, int leftBound, int rightBound) {
		this.vpanel = powerVsTimePanel;
		this.spectrumBrowser = mSpectrumBrowser;
		this.freq = currentFreq;
		this.width = canvasPixelWidth;
		this.height = canvasPixelHeight;
		this.sensorId = mSensorId;
		this.selectionTime = mSelectionTime;
		this.spectrumBrowser.getSpectrumBrowserService().generatePowerVsTime(
				sensorId, selectionTime, currentFreq, leftBound, rightBound,
				this);

	}

	public PowerVsTime(SpectrumBrowser mSpectrumBrowser,
			VerticalPanel powerVsTimePanel, String mSensorId,
			long mSelectionTime, long currentFreq, int canvasPixelWidth,
			int canvasPixelHeight) {
		this.vpanel = powerVsTimePanel;
		this.spectrumBrowser = mSpectrumBrowser;
		this.freq = currentFreq;
		this.width = canvasPixelWidth;
		this.height = canvasPixelHeight;
		this.sensorId = mSensorId;
		this.selectionTime = mSelectionTime;
		this.spectrumBrowser.getSpectrumBrowserService().generatePowerVsTime(
				sensorId, selectionTime, currentFreq, this);

	}

	private void handleImageLoadEvent() {
		RootPanel.get().remove(spectrumImage);
		spectrumImage.setPixelSize(width, height);
		spectrumImage.setVisible(true);
		vpanel.add(spectrumImage);
	}

	protected float round2(double val) {
		return (float) ((int) ((val + .005) * 100) / 100.0);
	}

	@Override
	public void onSuccess(String result) {
		try {
			JSONValue jsonValue = JSONParser.parseLenient(result);
			if (jsonValue.isObject().get(Defines.STATUS).equals(Defines.OK)) {
				logger.log(Level.SEVERE, "Error retrieving data");
				spectrumBrowser.displayError("Error retrieving data");
				return;
			}
			if (jsonValue.isObject().get("timeArray") != null) {
				// If data values are available then plot an active chart.
				// if the time interval is too big then data values may not be supplied.
				final JSONArray timeArray = jsonValue.isObject()
						.get("timeArray").isArray();
				final JSONArray powerValues = jsonValue.isObject()
						.get("powerValues").isArray();
				final String title = jsonValue.isObject().get("title")
						.isString().stringValue();
				final String xlabel = jsonValue.isObject().get("xlabel")
						.isString().stringValue();
				final String ylabel = jsonValue.isObject().get("ylabel")
						.isString().stringValue();
				ChartLoader chartLoader = new ChartLoader(
						ChartPackage.CORECHART);

				chartLoader.loadApi(new Runnable() {

					@Override
					public void run() {
						DataTable dataTable = DataTable.create();
						dataTable.addRows(timeArray.size());
						dataTable.addColumn(ColumnType.NUMBER, xlabel);
						dataTable.addColumn(ColumnType.NUMBER, ylabel);

						for (int i = 0; i < timeArray.size(); i++) {

							double time = timeArray.get(i).isNumber()
									.doubleValue();
							double powerValue = powerValues.get(i).isNumber()
									.doubleValue();
							dataTable.setCell(i, 0,time,
								xlabel + " : " + Float.toString(round2(time)) );
							dataTable
									.setCell(i, 1,powerValue, ylabel + " : "  + Float.toString(round2(powerValue)));

						}

						ScatterChart powerVsTimeChart = new ScatterChart();
						powerVsTimeChart.setHeight(height + "px");
						powerVsTimeChart.setWidth(width + "px");
						powerVsTimeChart.setPixelSize(width, height);
						ScatterChartOptions options = ScatterChartOptions
								.create();
						options.setBackgroundColor("#f0f0f0");
						options.setPointSize(2);
						options.setHeight(height);
						options.setWidth(width);
						HAxis haxis = HAxis.create(xlabel);
						VAxis vaxis = VAxis.create(ylabel);
						options.setHAxis(haxis);
						options.setVAxis(vaxis);
						Legend legend = Legend.create(LegendPosition.NONE);
						options.setLegend(legend);						
						powerVsTimeChart.draw(dataTable,options);
						HTML html = new HTML("<h3>" + title + "</h3>");
						vpanel.add(html);
						vpanel.add(powerVsTimeChart);
					}
				});

			} else {

				url = jsonValue.isObject().get("powervstime").isString()
						.stringValue();
				spectrumImage = new FitImage();
				// spectrumImage.setWidth("100%");
				spectrumImage.setPixelSize(height, width);
				// image.setFixedWidth(canvasPixelWidth);
				spectrumImage.addLoadHandler(new LoadHandler() {

					@Override
					public void onLoad(LoadEvent event) {

						logger.fine("Image loaded");
						handleImageLoadEvent();

					}

				});
				spectrumImage.setVisible(false);
				spectrumImage.setUrl(url);
				RootPanel.get().add(spectrumImage);
			}

		} catch (Throwable th) {
			logger.log(Level.SEVERE, "Error parsing returned JSON ", th);
			spectrumBrowser.displayError("Error communicating with server ");
		}

	}

	@Override
	public void onFailure(Throwable throwable) {
		// TODO Auto-generated method stub

	}

}
