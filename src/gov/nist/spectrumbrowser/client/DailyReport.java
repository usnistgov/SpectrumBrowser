package gov.nist.spectrumbrowser.client;

import java.util.Date;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.dom.client.ImageElement;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.ErrorEvent;
import com.google.gwt.event.dom.client.ErrorHandler;
import com.google.gwt.event.dom.client.LoadEvent;
import com.google.gwt.event.dom.client.LoadHandler;
import com.google.gwt.json.client.JSONObject;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Panel;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.reveregroup.gwt.imagepreloader.FitImage;
import com.smartgwt.client.widgets.toolbar.ToolStrip;
import com.smartgwt.client.widgets.toolbar.ToolStripButton;

public class DailyReport {
	

	private static final Logger logger = Logger.getLogger(SpectrumBrowser.class
			.getName());
	private VerticalPanel verticalPanel;
	private int imagePixelWidth;
	private int imagePixelHeight;
	private SpectrumBrowser spectrumBrowser;
	private HorizontalPanel spectrogramPanel;
	private Spectrogram spectrogram;
	private VerticalPanel statisticsPanel;
	private SpectrumLocationSelection locationSelection;
	private long dayBoundary;
	private String sessionId;
	private int minPower;
	private long minFreq;
	private long maxFreq;
	private long minDate;
	private long maxDate;
	private static long milisecPerDay = 24*60*60*1000;
	
	public class DailyReportImageLoadHandler implements LoadHandler {
		Image image;
		Panel panel;

		public DailyReportImageLoadHandler(Image image, Panel panel) {
			this.image = image;
			this.panel = panel;
		}

		@Override
		public void onLoad(LoadEvent loadEvent) {

			logger.fine("DailyReport:Image loaded");
			RootPanel.get().remove(image);
			panel.add(image);
			image.setVisible(true);
		}

	}
	/**
	 * Generate a daily report for a specific day
	 * 
	 * @param spectrumBrowser
	 * @param dayBoundary
	 * @param minPower
	 */

	public DailyReport(SpectrumBrowser spectrumBrowser,
			Spectrogram spectrogram,
			SpectrumLocationSelection locationSelection,
			VerticalPanel verticalPanel, String sessionId, long dayBoundary,
			long minDate, long maxDate,
			long minFreq, long maxFreq,
			int minPower, int imagePixelWidth, int imagePixelHeight) {

		this.verticalPanel = verticalPanel;
		this.imagePixelWidth = imagePixelWidth;
		this.imagePixelHeight = imagePixelHeight;
		this.spectrumBrowser = spectrumBrowser;
		this.spectrogram = spectrogram;
		this.locationSelection = locationSelection;
		this.dayBoundary = dayBoundary;
		this.sessionId = sessionId;
		this.minPower = minPower;
		this.minFreq = minFreq;
		this.maxFreq = maxFreq;
		this.minDate = minDate;
		this.maxDate = maxDate;
	}
	
	
	public void draw() {
	

		spectrumBrowser.getSpectrumBrowserService().generateDailyStatistics(
				sessionId, locationSelection.getLocation(), dayBoundary,
				minFreq, maxFreq,
				minPower, new SpectrumBrowserCallback<String>() {

					@Override
					public void onFailure(Throwable th) {
						Window.alert("Error communicating with the server");
						
						logger.log(Level.SEVERE,
								"problem communicating with the server", th);
						spectrumBrowser.displayError("Error communicating with the server");

					}

					@Override
					public void onSuccess(String jsonString) {
						try {
							logger.fine("generated daily report");
							JSONObject jsonObject = (JSONObject) JSONParser
									.parseStrict(jsonString);
							if ( jsonObject.get("spectrogram") == null) {
								Window.alert("No data");
								return;
							}
							verticalPanel.clear();
							
							ToolStrip toolStrip = new ToolStrip();
							
							ToolStripButton helpButton = new ToolStripButton("Help");
							toolStrip.addButton(helpButton);
							helpButton.setStyleName(".helpButton");
							
							ToolStripButton backButton = new ToolStripButton("Back to Sectrogram");
							backButton.setBorder("2px solid green");
							toolStrip.addButton(backButton);
							backButton.addClickHandler(new com.smartgwt.client.widgets.events.ClickHandler() {

						
								@Override
								public void onClick(
										com.smartgwt.client.widgets.events.ClickEvent event) {
									DailyReport.this.verticalPanel.clear();
									DailyReport.this.spectrogram.redraw();
								}
							});
							
							
							ToolStripButton backToLocationSelection = new ToolStripButton("Back to location selection");
							backToLocationSelection.setBorder("2px solid green");
							toolStrip.addButton(backToLocationSelection);
							backToLocationSelection.addClickHandler
							(new com.smartgwt.client.widgets.events.ClickHandler(){

								@Override
								public void onClick(
										com.smartgwt.client.widgets.events.ClickEvent event) {
									verticalPanel.clear();
									locationSelection.draw();
									
								}});
							
							ToolStripButton logoffButton = new ToolStripButton("Log off");
							logoffButton.setBorder("2px solid red");
							logoffButton.addClickHandler(new com.smartgwt.client.widgets.events.ClickHandler(){

								@Override
								public void onClick(
										com.smartgwt.client.widgets.events.ClickEvent event) {
										verticalPanel.clear();
										spectrumBrowser.logoff();
									
								}});
							
							toolStrip.addButton(logoffButton);
							
							verticalPanel.add(toolStrip);
							
							
							
							HTML html = new HTML("<h1>Daily report for "
									+ locationSelection.getLocation() + " Date : "
									+ locationSelection.formatDate(dayBoundary));
							verticalPanel.add(html);
							
							// set up the layout.
							HorizontalPanel spectrogramBackPanel = new HorizontalPanel();
							spectrogramBackPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
							VerticalPanel prevDayButtonPanel = new VerticalPanel();
							prevDayButtonPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_BOTTOM);
							Button prevDayButton = new Button();
							prevDayButton.setHTML("<img border='0' src='left-arrow.png' />");
							prevDayButtonPanel.add(prevDayButton);
							VerticalPanel nextDayButtonPanel = new VerticalPanel();
							nextDayButtonPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_BOTTOM);
							Button nextDayButton = new Button();
							nextDayButton.setHTML("<img border='0' src='right-arrow.png' />");
							nextDayButtonPanel.add(nextDayButton);
							
							prevDayButton.addClickHandler(new ClickHandler() {

								@Override
								public void onClick(ClickEvent clickEvent) {
									if (dayBoundary - milisecPerDay >= minDate ) {
										dayBoundary -= milisecPerDay;
										draw();
									}
									
								}} );
							
							nextDayButton.addClickHandler( new ClickHandler(){

								@Override
								public void onClick(ClickEvent clickHandler) {
									// TODO Auto-generated method stub
									if ( dayBoundary + milisecPerDay <= maxDate) {
										dayBoundary += milisecPerDay;
										draw();
									}
									
								}});
							

							spectrogramPanel = new HorizontalPanel();
							spectrogramPanel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
							spectrogramBackPanel.add(prevDayButton);
							spectrogramBackPanel.add(spectrogramPanel);
							spectrogramBackPanel.add(nextDayButton);
							
							
							
							// TBD add buttons to get prev and next days stats.
							statisticsPanel = new VerticalPanel();
							verticalPanel.add(spectrogramBackPanel);
							verticalPanel.add(statisticsPanel);
						
						
							String spectrogramImage = (String) jsonObject
									.get("spectrogram").isString()
									.stringValue();
							logger.fine("DailyReport: imageName = "
									+ spectrogramImage);
							String spectrogramUrl = DailyReport.this.spectrumBrowser
									.getBaseUrl()
									+ "getspectrogram?image="
									+ spectrogramImage;
							setImageUrl(spectrogramUrl,spectrogramPanel);
							String dailyM4Image = jsonObject.get("m4chart")
									.isString().stringValue();
							String dailyM4Url = DailyReport.this.spectrumBrowser
									.getBaseUrl()
									+ "getspectrogram?image="
									+ dailyM4Image;
							setImageUrl(dailyM4Url,statisticsPanel);
							String bandOccupancyImage = (String) jsonObject
									.get("occupancy").isString()
									.stringValue();
							String bandOccupancyUrl = DailyReport.this.spectrumBrowser
									.getBaseUrl()
									+ "getspectrogram?image=" + bandOccupancyImage;
							setImageUrl(bandOccupancyUrl,statisticsPanel);
						} catch (Exception ex) {
							logger.log(Level.SEVERE,
									"Error parsing returned value", ex);
						}

					}
				});

	}


	private void setImageUrl(String url, Panel panel) {
		Image image = new Image();
		image.setWidth(imagePixelWidth + "px");
		// image.setFixedWidth(canvasPixelWidth);
		image.addLoadHandler(new DailyReportImageLoadHandler(image, panel));
		image.setVisible(false);

		ImageElement imageElement = ImageElement.as(image.getElement());
		imageElement.setAttribute("HEIGHT", imagePixelHeight + "px");
		image.setHeight(imagePixelHeight + "px");

		logger.log(Level.FINER, "Setting URL " + url);
		image.addErrorHandler(new ErrorHandler() {

			@Override
			public void onError(ErrorEvent event) {
				logger.log(Level.SEVERE, "Error loading image");
				Window.alert("Error loading image");

			}
		});

		image.setUrl(url);
		RootPanel.get().add(image);

	}

}
