package gov.nist.spectrumbrowser.client;

import gov.nist.spectrumbrowser.common.SpectrumBrowserCallback;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.core.client.GWT;
import com.google.gwt.event.dom.client.LoadEvent;
import com.google.gwt.event.dom.client.LoadHandler;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.reveregroup.gwt.imagepreloader.FitImage;

public class PowerVsTime implements SpectrumBrowserCallback<String> {

	private VerticalPanel powerVsTimePanel;
	private SpectrumBrowser spectrumBrowser;
	private long freq;
	private int width;
	private int height;
	private String sensorId;
	private long selectionTime;
	private String url;
	private FitImage spectrumImage;
	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	public PowerVsTime(SpectrumBrowser mSpectrumBrowser,
			VerticalPanel powerVsTimePanel, String mSensorId,
			long mSelectionTime, long currentFreq, int canvasPixelWidth,
			int canvasPixelHeight, int leftBound, int rightBound) {
		this.powerVsTimePanel = powerVsTimePanel;
		this.spectrumBrowser = mSpectrumBrowser;
		this.freq = currentFreq;
		this.width = canvasPixelWidth;
		this.height = canvasPixelHeight;
		this.sensorId = mSensorId;
		this.selectionTime = mSelectionTime;
		this.spectrumBrowser.getSpectrumBrowserService().generatePowerVsTime( sensorId, selectionTime, currentFreq, leftBound, rightBound, this);

	}
	public PowerVsTime(SpectrumBrowser mSpectrumBrowser,
			VerticalPanel powerVsTimePanel, String mSensorId,
			long mSelectionTime, long currentFreq, int canvasPixelWidth,
			int canvasPixelHeight) {
		this.powerVsTimePanel = powerVsTimePanel;
		this.spectrumBrowser = mSpectrumBrowser;
		this.freq = currentFreq;
		this.width = canvasPixelWidth;
		this.height = canvasPixelHeight;
		this.sensorId = mSensorId;
		this.selectionTime = mSelectionTime;
		this.spectrumBrowser.getSpectrumBrowserService().generatePowerVsTime(sensorId, selectionTime, currentFreq, this);

	}
	private void handleImageLoadEvent() {
		RootPanel.get().remove(spectrumImage);
		spectrumImage.setPixelSize(width, height);
		spectrumImage.setVisible(true);
		powerVsTimePanel.add(spectrumImage);
	}

	@Override
	public void onSuccess(String result) {
		try {
			JSONValue jsonValue = JSONParser.parseLenient(result);
			url = jsonValue.isObject().get("powervstime")
					.isString().stringValue();
			spectrumImage = new FitImage();
			spectrumImage.setWidth(width + "px");
			spectrumImage.setPixelSize(width, width);
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
