package gov.nist.spectrumbrowser.client;

import java.util.logging.Logger;

import com.google.gwt.event.dom.client.LoadEvent;
import com.google.gwt.event.dom.client.LoadHandler;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.reveregroup.gwt.imagepreloader.FitImage;

public class PowerSpectrum implements SpectrumBrowserCallback<String> {
	
	private VerticalPanel vpanel;
	private SpectrumBrowser spectrumBrowser;
	private long milisecondOffset;
	private String imageUrl;
	private String sensorId;
	private long startTime;
	private FitImage spectrumImage;
	private String url;
	private int width;
	private int height;
	
	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	public PowerSpectrum(SpectrumBrowser spectrumBrowser, VerticalPanel vpanel,
			String sensorId, long startTime, long milisecondOffset, int width, int height) {
		this.vpanel = vpanel;
		this.spectrumBrowser = spectrumBrowser;
		this.milisecondOffset = milisecondOffset;
		this.sensorId = sensorId;
		this.startTime = startTime;
		this.width = width;
		this.height = height;
		this.spectrumBrowser.getSpectrumBrowserService().generateSpectrum(spectrumBrowser.getSessionId(), 
				sensorId,startTime,milisecondOffset, this);
	}

	private void handleImageLoadEvent() {
		RootPanel.get().remove(spectrumImage);
		spectrumImage.setPixelSize(width, height);
		spectrumImage.setVisible(true);
		vpanel.add(spectrumImage);
	}
	@Override
	public void onSuccess(String result) {
		
		JSONValue jsonValue = JSONParser.parseLenient(result);
		String spectrumFile = jsonValue.isObject().get("spectrum").isString().stringValue();
		url = SpectrumBrowser.getGeneratedDataPath()
		+ spectrumFile;
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

		
	}

	@Override
	public void onFailure(Throwable throwable) {
		spectrumBrowser.displayError("Error communicating with the server");
	}

}
