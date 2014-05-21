package gov.nist.spectrumbrowser.client;

import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.json.client.JSONArray;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.kiouri.sliderbar.client.event.BarValueChangedEvent;
import com.kiouri.sliderbar.client.event.BarValueChangedHandler;
import com.kiouri.sliderbar.client.solution.simplevertical.SliderBarSimpleVertical;
import com.smartgwt.client.widgets.toolbar.ToolStrip;
import com.smartgwt.client.widgets.toolbar.ToolStripButton;

public class Spectrogram {

	private VerticalPanel verticalPanel;
	private long minDate;
	private long minFreq;
	private long maxFreq;
	private long maxDate;
	private String location;
	private SpectrumBrowser spectrumBrowser;
	private SpectrumLocationSelection spectrumLocationSelection;
	private String sessionId;
	private SpectrogramFragment spectrogramFragment;
	int maxPower;
	int minPower;
	private int occupancyMinPower;
	private SliderBarSimpleVertical occupancyMinPowerSliderBar;
	private Label occupancyMinPowerLabel;
	private long absMinDate;
	private long absMaxDate;
	private int canvasYmax;
	private int canvasXmax;
	private int occupancyBarValue;

	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	public class SpectrogramDragHandler {
		public void drag(long drag) {
			if (minDate + drag < absMinDate) {
				minDate = absMinDate;
			} else {
				minDate += drag;
			}

			if (maxDate + drag > absMaxDate) {
				maxDate = absMaxDate;
			} else {
				maxDate += drag;
			}
			verticalPanel.clear();
			Spectrogram.this.draw();
		}
	}

	public class OccupancyMinPowerSliderHandler implements
			BarValueChangedHandler {
		Label occupancyMinPowerLabel;
	
		public OccupancyMinPowerSliderHandler(Label occupancyMinPowerLabel) {
			occupancyMinPowerSliderBar.setValue(100);
			this.occupancyMinPowerLabel = occupancyMinPowerLabel;
			occupancyMinPowerLabel.setText(minPower + " dBm");
			this.occupancyMinPowerLabel
					.setTitle("Power Cutoff for Occupancy Graph");
		}

		@Override
		public void onBarValueChanged(BarValueChangedEvent event) {
			try {

				occupancyBarValue = occupancyMinPowerSliderBar.getValue();
				logger.log(Level.FINEST, "bar value changed new value is "
						+ occupancyBarValue);
				occupancyMinPower = (int) ((1 - (double) occupancyBarValue / 100.0)
						* (maxPower - minPower) + minPower);
				occupancyMinPowerLabel.setText(Integer
						.toString((int) occupancyMinPower) + " dBm");
				spectrogramFragment.setMinMaxPower(occupancyMinPower, maxPower,
						minPower);

			} catch (Exception ex) {
				logger.log(Level.SEVERE, " Exception ", ex);
			}

		}

	}

	private class SpectrogramRegionGetter implements SpectrumBrowserCallback<String> {

		public SpectrogramRegionGetter() {

		}

		public void getRegions() {
			spectrumBrowser.getSpectrumBrowserService().getSpectrogramRegions(
					sessionId, location, minDate, maxDate, minFreq, maxFreq,
					this);
		}

		@Override
		public void onFailure(Throwable arg0) {
			spectrumBrowser
					.displayError("SpectrogramRegionGetter: Error in communicating with the server");
		}

		@Override
		public void onSuccess(String jsonString) {
			try {
				logger.log(Level.FINER, "getRegions returned " + jsonString);
				JSONValue jsonValue = JSONParser.parseLenient(jsonString);
				JSONArray timeArray = jsonValue.isObject().get("timeRanges")
						.isArray();
				JSONArray freqArray = jsonValue.isObject().get("freqRanges")
						.isArray();

				JSONArray deadRegions = jsonValue.isObject().get("deadRegions")
						.isArray();

				JSONArray powerArray = jsonValue.isObject().get("powerRanges")
						.isArray();
				minPower = Integer.parseInt(powerArray.get(0).isString()
						.stringValue());
				maxPower = Integer.parseInt(powerArray.get(1).isString()
						.stringValue());
				occupancyMinPower = minPower;
				spectrogramFragment
						.setMinMaxPower(minPower, maxPower, minPower);
				Spectrogram.this.occupancyMinPowerLabel.setText(Integer
						.toString((int) minPower) + " dBm");

				if (deadRegions.size() != 0) {
					long tmin[] = new long[deadRegions.size()];
					long tmax[] = new long[deadRegions.size()];

					for (int i = 0; i < deadRegions.size(); i++) {
						String timeRange = deadRegions.get(i).isString()
								.stringValue();
						logger.log(Level.FINER, "deadRegion : " + timeRange);
						String[] timeRanges = timeRange.split(",");
						tmin[i] = Long.parseLong(timeRanges[0]);
						tmax[i] = Long.parseLong(timeRanges[1]);
					}

					for (int i = 0; i < tmin.length; i++) {
						spectrogramFragment.addDeadRegion(tmin[i], tmax[i]);
					}
				}
			    minDate = System.currentTimeMillis();
				maxDate = 0;
				for( int i = 0 ; i < timeArray.size(); i++) {
					String[] minmaxtimes = timeArray.get(i).isString().stringValue().split(",");
					long tmin = Long.parseLong(minmaxtimes[0]);
					long tmax = Long.parseLong(minmaxtimes[1]);
					if ( tmin < minDate) minDate = tmin;
					if ( tmax > maxDate) maxDate = tmax;
					
				}
				spectrogramFragment.setMinMaxDates(minDate,maxDate);
				

				if (timeArray.size() != 0) {
					new SpectrogramGetter(maxPower, minPower).getSpectrogram();
				} else {
					Window.alert("No sectrogram readings in the given range");
					logger.log(Level.FINER,
							"SpectrogramRegionGetter: timeArray.size() = 0");
					verticalPanel.clear();
					spectrumLocationSelection.draw();
					return;
				}
			} catch (Exception ex) {
				logger.log(Level.SEVERE, "Exception occured ", ex);
			}
		}

	}

	private class SpectrogramGetter implements SpectrumBrowserCallback<String> {
		int pmax;
		int pmin;

		public SpectrogramGetter(int maxPower, int minPower) {
			logger.log(Level.FINER, "SpectrogramGetter: minPower : " + minPower
					+ " maxPower " + maxPower);
			pmax = maxPower;
			pmin = minPower;
		}

		@Override
		public void onFailure(Throwable ex) {
			spectrumBrowser.displayError("Error sending req. to server");
			logger.log(Level.SEVERE, "Error sending request to the server", ex);
		}

		@Override
		public void onSuccess(String jsonString) {

			try {
				logger.log(Level.FINER, "spectrogramGetter: retrieved "
						+ jsonString.length() + " bytes");
				JSONObject jsonObject = (JSONObject) JSONParser
						.parseStrict(jsonString);
				if (jsonObject.get("image") != null
						&& jsonObject.get("cmap") != null) {
					String image = jsonObject.get("image").isString()
							.stringValue();
					String cmapImage = jsonObject.get("cmap").isString()
							.stringValue();
					String url = spectrumBrowser.getBaseUrl()
							+ "getspectrogram?image=" + image;
					logger.log(Level.FINER, "URL = " + url);
					String cmapUrl = spectrumBrowser.getBaseUrl()
							+ "getspectrogram?image=" + cmapImage;
					logger.log(Level.FINER, "CMAP URL = " + cmapUrl);
					spectrogramFragment.setSpectrogramImage(url, cmapUrl);

					logger.log(Level.FINE,
							"Done retrieving and drawing spectrum");
				} else {
					logger.log(Level.SEVERE,
							"Image not generated -- check the logs!");
				}

			} catch (Exception ex) {
				logger.log(Level.SEVERE, "Error parsing json", ex);

			}

		}

		public void getSpectrogram() {
			String url = spectrumBrowser.getBaseUrl()
					+ "getspectrogram?image=" + "/computing-spectrogram-please-wait.png";
			spectrogramFragment.setSpectrogramImage(url, null);
			spectrumBrowser.getSpectrumBrowserService().generateSpectrogram(
					sessionId, location, minDate, maxDate, minFreq, maxFreq,
					pmin, pmax, this);
		}
	}

	/**
	 * Draw the spectrogram for the given region.
	 * 
	 * @param sessionId
	 * @param spectrumBrowser
	 * @param spectrumLocationSelection
	 * @param location
	 * @param minDate
	 * @param maxDate
	 * @param absMinDate
	 * @param absMaxDate
	 * @param minFreq
	 * @param maxFreq
	 * @param verticalPanel
	 */
	public Spectrogram(String sessionId, SpectrumBrowser spectrumBrowser,
			SpectrumLocationSelection spectrumLocationSelection,
			String location, long minDate, long maxDate, long absMinDate,
			long absMaxDate, long minFreq, long maxFreq,
			VerticalPanel verticalPanel) {

		this.sessionId = sessionId;
		this.spectrumBrowser = spectrumBrowser;
		this.verticalPanel = verticalPanel;

		this.location = location;
		this.minFreq = minFreq;
		this.maxFreq = maxFreq;
		this.minDate = minDate;
		this.maxDate = maxDate;
		this.absMinDate = absMinDate;
		this.absMaxDate = absMaxDate;

		// Save this for back button.
		this.canvasYmax = 400;
		this.canvasXmax = 800;
		this.spectrumLocationSelection = spectrumLocationSelection;
		this.draw();
	}
	
	private void drawNavigation() {
		ToolStrip toolStrip = new ToolStrip();
		
		ToolStripButton helpButton = new ToolStripButton("Help");
		helpButton.setStyleName(".helpbutton");
		toolStrip.addButton(helpButton);
		ToolStripButton backButton = new ToolStripButton(
				"Back to region and range selection.");
		backButton.setBorder("2px solid green");
		backButton.addClickHandler(new com.smartgwt.client.widgets.events.ClickHandler() {

			@Override
			public void onClick(com.smartgwt.client.widgets.events.ClickEvent clickEvent) {
				Spectrogram.this.verticalPanel.clear();
				Spectrogram.this.spectrumLocationSelection.draw();

			}
		});
		toolStrip.addButton(backButton);
		
		ToolStripButton logoffButton = new ToolStripButton("Log off");
		logoffButton.setBorder("2px solid red");
		toolStrip.addButton(logoffButton);
		logoffButton.addClickHandler(new com.smartgwt.client.widgets.events.ClickHandler(){

			@Override
			public void onClick(
					com.smartgwt.client.widgets.events.ClickEvent event) {
				spectrumBrowser.logoff();
				
			}});
		verticalPanel.add(toolStrip);
		HTML html = new HTML("<H1> Spectrogram for " + location + "</H1>",
				true);
		verticalPanel.add(html);
	}
	
	public void redraw() {
		
		drawNavigation();
		
		this.spectrogramFragment.draw();
	
		
		

		HorizontalPanel hpanel = new HorizontalPanel();

		hpanel.add(spectrogramFragment);
		// Occupancy min power slider bar.
		VerticalPanel occupancyMinPowerVpanel = new VerticalPanel();
		occupancyMinPowerSliderBar.removeFromParent();
		this.occupancyMinPowerSliderBar = new SliderBarSimpleVertical(100,
				canvasYmax + "px", true);
		occupancyMinPowerVpanel.add(occupancyMinPowerSliderBar);
		occupancyMinPowerSliderBar.setMaxValue(100);

		
		occupancyMinPowerVpanel
				.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
		occupancyMinPowerVpanel
				.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
		this.occupancyMinPowerLabel = new Label();
		occupancyMinPowerVpanel.add(occupancyMinPowerLabel);
		Button generateSpectrogramButton = new Button("Cutoff and Redraw");
		occupancyMinPowerVpanel.add(generateSpectrogramButton);
		occupancyMinPowerSliderBar
				.addBarValueChangedHandler(new OccupancyMinPowerSliderHandler(
						occupancyMinPowerLabel));
		occupancyMinPowerSliderBar.setValue(occupancyBarValue);

		// hpanel.add(occupancyMinPowerVpanel);
		spectrogramFragment
				.addOccupancyMinPowerPanel(occupancyMinPowerVpanel);

		verticalPanel.add(hpanel);
		verticalPanel
				.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);

		generateSpectrogramButton.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent arg0) {
				new SpectrogramGetter(maxPower, occupancyMinPower)
						.getSpectrogram();
			}
		});
		
		
		spectrogramFragment.handleSpectrogramLoadEvent();

	}

	public void draw() {

		try {
			drawNavigation();

			this.spectrogramFragment = new SpectrogramFragment(minDate,
					maxDate, minFreq, maxFreq, canvasXmax, canvasYmax,
					sessionId, spectrumLocationSelection, spectrumBrowser,
					verticalPanel,
					Spectrogram.this,
					new SpectrogramDragHandler());
			this.spectrogramFragment.draw();
			

			HorizontalPanel hpanel = new HorizontalPanel();

			hpanel.add(spectrogramFragment);
			// Occupancy min power slider bar.
			VerticalPanel occupancyMinPowerVpanel = new VerticalPanel();
			this.occupancyMinPowerSliderBar = new SliderBarSimpleVertical(100,
					canvasYmax + "px", true);
			occupancyMinPowerVpanel.add(occupancyMinPowerSliderBar);
			occupancyMinPowerSliderBar.setMaxValue(100);
			occupancyMinPowerVpanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
			occupancyMinPowerVpanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
			this.occupancyMinPowerLabel = new Label();
			occupancyMinPowerVpanel.add(occupancyMinPowerLabel);
			Button generateSpectrogramButton = new Button("Cutoff and Redraw");
			occupancyMinPowerVpanel.add(generateSpectrogramButton);
			occupancyMinPowerSliderBar
					.addBarValueChangedHandler(new OccupancyMinPowerSliderHandler(
							occupancyMinPowerLabel));
			occupancyMinPowerSliderBar.setValue(100);
			// hpanel.add(occupancyMinPowerVpanel);
			spectrogramFragment
					.addOccupancyMinPowerPanel(occupancyMinPowerVpanel);

			verticalPanel.add(hpanel);
			verticalPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);

			generateSpectrogramButton.addClickHandler(new ClickHandler() {

				@Override
				public void onClick(ClickEvent arg0) {
					new SpectrogramGetter(maxPower, occupancyMinPower)
							.getSpectrogram();
				}
			});
		

			new SpectrogramRegionGetter().getRegions();
		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Exception ", ex);
		}
	}

}
