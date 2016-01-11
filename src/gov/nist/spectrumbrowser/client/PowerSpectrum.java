package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.LoadEvent;
import com.google.gwt.event.dom.client.LoadHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.googlecode.gwt.charts.client.ChartLoader;
import com.googlecode.gwt.charts.client.ChartPackage;
import com.googlecode.gwt.charts.client.ColumnType;
import com.googlecode.gwt.charts.client.DataTable;
import com.googlecode.gwt.charts.client.corechart.LineChartOptions;
import com.googlecode.gwt.charts.client.corechart.ScatterChart;
import com.googlecode.gwt.charts.client.corechart.ScatterChartOptions;
import com.googlecode.gwt.charts.client.options.HAxis;
import com.googlecode.gwt.charts.client.options.VAxis;
import com.reveregroup.gwt.imagepreloader.FitImage;

public class PowerSpectrum implements SpectrumBrowserCallback<String> {

	private VerticalPanel vpanel;
	private SpectrumBrowser spectrumBrowser;
	private int width;
	private int height;
	private String sensorId;

	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	public PowerSpectrum(SpectrumBrowser spectrumBrowser, VerticalPanel vpanel,
			String sensorId, long startTime, long milisecondOffset, int width,
			int height) {
		this.sensorId = sensorId;
		this.vpanel = vpanel;
		this.spectrumBrowser = spectrumBrowser;
		this.width = width;
		this.height = height;
		this.spectrumBrowser.getSpectrumBrowserService().generateSpectrum(
				sensorId, startTime, milisecondOffset, this);
	}

	public PowerSpectrum(SpectrumBrowser spectrumBrowser, VerticalPanel vpanel,
			String sensorId, long startTime, double hourOffset, int width,
			int height) {
		int secondOffset = (int) (hourOffset * 60 * 60);
		this.sensorId = sensorId;
		this.spectrumBrowser = spectrumBrowser;
		this.width = width;
		this.height = height;
		this.vpanel = vpanel;
		this.spectrumBrowser.getSpectrumBrowserService().generateSpectrum(
				sensorId, startTime, secondOffset, this);
	}

	public PowerSpectrum(SpectrumBrowser spectrumBrowser, VerticalPanel vpanel,
			String sensorId, long startTime, double hourOffset,
			long subBandMinFreq, long subBandMaxFreq, int width, int height) {
		int secondOffset = (int) (hourOffset * 60 * 60);
		this.spectrumBrowser = spectrumBrowser;
		this.width = width;
		this.height = height;
		this.vpanel = vpanel;
		this.spectrumBrowser.getSpectrumBrowserService().generateSpectrum(
				sensorId, startTime, secondOffset, subBandMinFreq,
				subBandMaxFreq, this);
	}

	@Override
	public void onSuccess(String result) {

		JSONValue jsonValue = JSONParser.parseLenient(result);
		final JSONArray frequencyData = jsonValue.isObject().get("freqArray")
				.isArray();
		final JSONArray spectrumData = jsonValue.isObject().get("spectrumData")
				.isArray();
		final JSONArray noiseFloorData = jsonValue.isObject()
				.get("noiseFloorData").isArray();
		ChartLoader chartLoader = new ChartLoader(ChartPackage.CORECHART);

		chartLoader.loadApi(new Runnable() {
			@Override
			public void run() {
				try {
					DataTable dataTable = DataTable.create();
					dataTable.addRows(spectrumData.size());
					dataTable.addColumn(ColumnType.NUMBER, "Frequency (MHz)");
					dataTable.addColumn(ColumnType.NUMBER, "Signal");
					dataTable.addColumn(ColumnType.NUMBER, "Noise Floor");
					for (int i = 0; i < spectrumData.size(); i++) {
						double freq = frequencyData.get(i).isNumber()
								.doubleValue();
						double signalPower = spectrumData.get(i).isNumber()
								.doubleValue();
						double noiseFloor = noiseFloorData.get(i).isNumber()
								.doubleValue();
						dataTable.setCell(i, 0, freq, freq + " MHz");
						dataTable.setCell(i, 1, signalPower, signalPower + " dBm");
						dataTable.setCell(i, 2, noiseFloor, noiseFloor + " dBm");
					}
					ScatterChart spectrumChart = new ScatterChart();
					spectrumChart.setHeight(height + "px");
					spectrumChart.setWidth(width + "px");
					spectrumChart.setPixelSize(width, height);
					spectrumChart.setTitle("Power Spectrum");
					ScatterChartOptions options = ScatterChartOptions.create();
					options.setBackgroundColor("#f0f0f0");
					options.setPointSize(2);
					options.setHeight(height);
					options.setWidth(width);
					HAxis haxis = HAxis.create("Frequency (Hz)");
					VAxis vaxis = VAxis.create("Power (dBm)");
					options.setHAxis(haxis);
					options.setVAxis(vaxis);
					spectrumChart.draw(dataTable, options);
					
					vpanel.add(spectrumChart);
				} catch (Throwable th) {
					logger.log(Level.SEVERE,
							"Exception in processing response", th);
				}
			}
		});

	}

	@Override
	public void onFailure(Throwable throwable) {
		spectrumBrowser.displayError("Error communicating with the server");
	}

}
