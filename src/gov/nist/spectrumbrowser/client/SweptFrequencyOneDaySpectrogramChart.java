package gov.nist.spectrumbrowser.client;

import java.util.ArrayList;
import java.util.logging.Level;
import java.util.logging.Logger;

import com.google.gwt.canvas.client.Canvas;
import com.google.gwt.core.client.Duration;
import com.google.gwt.core.client.JsArray;
import com.google.gwt.core.client.Scheduler;
import com.google.gwt.dom.client.ImageElement;
import com.google.gwt.dom.client.Style.Unit;
import com.google.gwt.event.dom.client.ClickEvent;
import com.google.gwt.event.dom.client.ClickHandler;
import com.google.gwt.event.dom.client.ErrorEvent;
import com.google.gwt.event.dom.client.ErrorHandler;
import com.google.gwt.event.dom.client.LoadEvent;
import com.google.gwt.event.dom.client.LoadHandler;
import com.google.gwt.event.dom.client.MouseMoveEvent;
import com.google.gwt.event.dom.client.MouseMoveHandler;
import com.google.gwt.i18n.client.NumberFormat;
import com.google.gwt.json.client.JSONParser;
import com.google.gwt.json.client.JSONValue;
import com.google.gwt.safehtml.shared.SafeHtmlBuilder;
import com.google.gwt.user.client.Window;
import com.google.gwt.user.client.ui.Button;
import com.google.gwt.user.client.ui.Grid;
import com.google.gwt.user.client.ui.HTML;
import com.google.gwt.user.client.ui.HasHorizontalAlignment;
import com.google.gwt.user.client.ui.HasVerticalAlignment;
import com.google.gwt.user.client.ui.HorizontalPanel;
import com.google.gwt.user.client.ui.Image;
import com.google.gwt.user.client.ui.Label;
import com.google.gwt.user.client.ui.MenuBar;
import com.google.gwt.user.client.ui.RootPanel;
import com.google.gwt.user.client.ui.TabLayoutPanel;
import com.google.gwt.user.client.ui.TabPanel;
import com.google.gwt.user.client.ui.VerticalPanel;
import com.googlecode.gwt.charts.client.ChartLoader;
import com.googlecode.gwt.charts.client.ChartPackage;
import com.googlecode.gwt.charts.client.ColumnType;
import com.googlecode.gwt.charts.client.DataTable;
import com.googlecode.gwt.charts.client.Selection;
import com.googlecode.gwt.charts.client.corechart.ScatterChart;
import com.googlecode.gwt.charts.client.corechart.ScatterChartOptions;
import com.googlecode.gwt.charts.client.event.SelectEvent;
import com.googlecode.gwt.charts.client.event.SelectHandler;
import com.googlecode.gwt.charts.client.options.HAxis;
import com.googlecode.gwt.charts.client.options.VAxis;
import com.kiouri.sliderbar.client.event.BarValueChangedEvent;
import com.kiouri.sliderbar.client.event.BarValueChangedHandler;
import com.kiouri.sliderbar.client.solution.simplevertical.SliderBarSimpleVertical;
import com.reveregroup.gwt.imagepreloader.FitImage;
import com.reveregroup.gwt.imagepreloader.ImageLoadEvent;
import com.reveregroup.gwt.imagepreloader.ImageLoadHandler;
import com.reveregroup.gwt.imagepreloader.ImagePreloader;

public class SweptFrequencyOneDaySpectrogramChart implements
		SpectrumBrowserCallback<String> , SpectrumBrowserScreen{

	private static final String LABEL = "Single Day Spectrogram >>";
	private static final String END_LABEL = "Single Day Spectrogram";
	
	String mSensorId;
	SpectrumBrowser mSpectrumBrowser;
	long mSelectionTime;
	SpectrumBrowserShowDatasets mSpectrumBrowserShowDatasets;
	DailyStatsChart mDailyStatsChart;
	JSONValue jsonValue;
	public double currentTime;
	public double currentFreq;
	private VerticalPanel spectrumAndOccupancyPanel;
	int cutoff;
	int maxPower;
	int occupancyMinPower;
	Label currentValue = new Label("Click on spectrogram for power spectrum.");
	HorizontalPanel hpanel; // = new HorizontalPanel();
	VerticalPanel vpanel;// = new VerticalPanel();
	long maxTime;
	double minFreqMhz;
	double maxFreqMhz;
	int timeDelta;
	private double yPixelsPerMegahertz;
	private int canvasPixelWidth;
	private int canvasPixelHeight;
	private Label maxPowerLabel;
	private Label minPowerLabel;
	private VerticalPanel spectrogramPanel;
	private VerticalPanel freqPanel;
	private HorizontalPanel powerMapPanel;
	private Canvas spectrogramCanvas;
	private HorizontalPanel xaxisPanel;
	private FitImage powerMapImage;
	private Image spectrogramImage;
	private String localDateOfAcquisition;
	private String cmapUrl;
	private String spectrogramUrl;
	VerticalPanel occupancyPanel;
	private SliderBarSimpleVertical occupancyMinPowerSliderBar;
	private Label occupancyMinPowerLabel;
	private VerticalPanel occupancyMinPowerVpanel;
	private int minPower;
	private int noiseFloor;
	private long prevAcquisitionTime;
	private long nextAcquisitionTime;
	private ArrayList<Double> timeArray;
	private ArrayList<Double> occupancyArray;
	private ScatterChart occupancyChart;
	private TabPanel tabPanel;
	private Image pleaseWaitImage;
	private long tStartTimeUtc;
	private Grid grid;
	private long mMinFreq;
	private long mMaxFreq;
	private long mSubBandMinFreq;
	private long mSubBandMaxFreq;
	private String mSys2detect;

	private static Logger logger = Logger.getLogger("SpectrumBrowser");

	/**
	 * Update the time and frequency readings on top of the plot if the user
	 * moves the mouse around in the canvas area.
	 * 
	 */
	public class SurfaceMouseMoveHandlerImpl implements MouseMoveHandler {

		@Override
		public void onMouseMove(MouseMoveEvent event) {

			int timeCoord = event.getRelativeX(event.getRelativeElement());
			int freqCoord = event.getRelativeY(event.getRelativeElement());
			double xratio = ((double) timeCoord / (double) canvasPixelWidth);
			double yratio = 1.0 - ((double) freqCoord / (double) canvasPixelHeight);
			currentFreq = (long) ((maxFreqMhz - minFreqMhz) * yratio)
					+ minFreqMhz;
			currentTime = (((double) (maxTime * xratio)));
			NumberFormat nf = NumberFormat.getFormat("00.00");
			currentValue.setText("Hours Since Start of Day= "
					+ nf.format(currentTime) + " ; Freq = " + currentFreq
					+ " MHz");
		}

	}

	/*
	 * Callback for the selector that controls the cutoff power.
	 */
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

				int occupancyBarValue = occupancyMinPowerSliderBar.getValue();
				logger.log(Level.FINEST, "bar value changed new value is "
						+ occupancyBarValue);
				occupancyMinPower = (int) ((1 - (double) occupancyBarValue / 100.0)
						* (maxPower - minPower) + minPower);
				occupancyMinPowerLabel.setText(Integer
						.toString((int) occupancyMinPower) + " dBm");

			} catch (Exception ex) {
				logger.log(Level.SEVERE, " Exception ", ex);
			}

		}

	}

	public SweptFrequencyOneDaySpectrogramChart(String sensorId,
			long selectionTime, String sys2detect, long minFreq, long maxFreq,
			long subBandMinFreq, long subBandMaxFreq,
			VerticalPanel verticalPanel, SpectrumBrowser spectrumBrowser,
			SpectrumBrowserShowDatasets spectrumBrowserShowDatasets,
			DailyStatsChart dailyStatsChart, int width, int height) {
		mSensorId = sensorId;
		mSelectionTime = selectionTime;
		vpanel = verticalPanel;
		mSpectrumBrowser = spectrumBrowser;
		mSpectrumBrowserShowDatasets = spectrumBrowserShowDatasets;
		mDailyStatsChart = dailyStatsChart;
		mMinFreq = minFreq;
		mMaxFreq = maxFreq;
		mSys2detect = sys2detect;
		mSubBandMinFreq = subBandMinFreq;
		mSubBandMaxFreq = subBandMaxFreq;
		minFreqMhz = (double) (mSubBandMinFreq) / 1E6;
		maxFreqMhz = (double) (mSubBandMaxFreq) / 1E6;
		logger.finer("minFreq = " + minFreq + " minFreqMhz " + minFreqMhz
				+ " maxFeq " + maxFreq + " maxFreqMhz " + maxFreqMhz);

		ImagePreloader.load(SpectrumBrowser.getIconsPath()
				+ "computing-spectrogram-please-wait.png", null);
		pleaseWaitImage = new Image();
		vpanel.add(pleaseWaitImage);

		mSpectrumBrowser.getSpectrumBrowserService()
				.generateSingleDaySpectrogramAndOccupancy(
						mSpectrumBrowser.getSessionId(), sensorId,
						mSelectionTime,mSys2detect,  mMinFreq, mMaxFreq, mSubBandMinFreq,
						mSubBandMaxFreq, this);

	}

	@Override
	public void onSuccess(String result) {
		try {
			Duration duration = new Duration();
			// logger.finer("result = " + result);
			jsonValue = JSONParser.parseLenient(result);
			timeDelta = (int) jsonValue.isObject().get("timeDelta").isNumber()
					.doubleValue();
			String spectrogramFile = jsonValue.isObject().get("spectrogram")
					.isString().stringValue();
			canvasPixelWidth = (int) jsonValue.isObject().get("image_width")
					.isNumber().doubleValue();
			canvasPixelHeight = (int) jsonValue.isObject().get("image_height")
					.isNumber().doubleValue();
			String colorBarFile = jsonValue.isObject().get("cbar").isString()
					.stringValue();
			spectrogramUrl = SpectrumBrowser.getGeneratedDataPath()
					+ spectrogramFile;
			cmapUrl = SpectrumBrowser.getGeneratedDataPath() + colorBarFile;
			maxPower = (int) jsonValue.isObject().get("maxPower").isNumber()
					.doubleValue();
			cutoff = (int) jsonValue.isObject().get("cutoff").isNumber()
					.doubleValue();
			minPower = (int) jsonValue.isObject().get("minPower").isNumber()
					.doubleValue();

			noiseFloor = (int) jsonValue.isObject().get("noiseFloor")
					.isNumber().doubleValue();
			localDateOfAcquisition = jsonValue.isObject().get("formattedDate")
					.isString().stringValue();
			prevAcquisitionTime = (long) jsonValue.isObject()
					.get("prevAcquisition").isNumber().doubleValue();
			nextAcquisitionTime = (long) jsonValue.isObject()
					.get("nextAcquisition").isNumber().doubleValue();
			tStartTimeUtc = (long) jsonValue.isObject().get("tStartTimeUtc")
					.isNumber().doubleValue();
			maxTime = timeDelta;
			timeArray = new ArrayList<Double>();
			occupancyArray = new ArrayList<Double>();
			int nvalues = jsonValue.isObject().get("timeArray").isArray()
					.size();
			for (int i = 0; i < nvalues; i++) {
				timeArray.add(jsonValue.isObject().get("timeArray").isArray()
						.get(i).isNumber().doubleValue());
				occupancyArray.add(jsonValue.isObject().get("occupancyArray")
						.isArray().get(i).isNumber().doubleValue());
			}
			long elapsedTime = duration.elapsedMillis();
			logger.finer("Unpacking json object took " + elapsedTime);

		} catch (Throwable throwable) {
			logger.log(Level.SEVERE, result);
			logger.log(Level.SEVERE, "Error parsing json result from server",
					throwable);
			mSpectrumBrowser.displayError("Error parsing JSON");
		}
		draw();

	}

	private void drawNavigation() {
		MenuBar menuBar = new MenuBar();
		SafeHtmlBuilder safeHtml = new SafeHtmlBuilder();

		menuBar.addItem(safeHtml.appendEscaped(SpectrumBrowser.LOGOFF_LABEL)
				.toSafeHtml(), new Scheduler.ScheduledCommand() {

			@Override
			public void execute() {
				mSpectrumBrowser.logoff();

			}
		});

		menuBar.addItem(
				new SafeHtmlBuilder().appendEscaped(
						SpectrumBrowserShowDatasets.LABEL).toSafeHtml(),
				new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {
						mSpectrumBrowserShowDatasets.draw();
					}
				});

		menuBar.addItem(
				new SafeHtmlBuilder().appendEscaped(DailyStatsChart.LABEL)
						.toSafeHtml(), new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {
						mDailyStatsChart.draw();
					}
				});

		

		menuBar.addItem(
				new SafeHtmlBuilder().appendEscaped(SpectrumBrowser.HELP_LABEL)
						.toSafeHtml(), new Scheduler.ScheduledCommand() {

					@Override
					public void execute() {
						// TODO Auto-generated method stub

					}
				});
		vpanel.add(menuBar);

	}

	/**
	 * This is called after the spectrogram has loaded from the server. Also
	 * gets called when we want to redraw the spectrogram.
	 * 
	 */
	private void handleSpectrogramLoadEvent() {
		RootPanel.get().remove(spectrogramImage);

		spectrogramImage.setVisible(true);

		ImageElement imageElement = ImageElement.as(spectrogramImage
				.getElement());

		Canvas canvas = Canvas.createIfSupported();
		if (spectrogramCanvas != null) {
			spectrogramPanel.remove(spectrogramCanvas);
			spectrogramPanel.remove(xaxisPanel);
		}
		spectrogramCanvas = canvas;
		spectrogramCanvas.setCoordinateSpaceHeight(canvasPixelHeight);
		spectrogramCanvas.setCoordinateSpaceWidth(canvasPixelWidth);
		spectrogramCanvas
				.addMouseMoveHandler(new SurfaceMouseMoveHandlerImpl());

		spectrogramCanvas.addClickHandler(new ClickHandler() {

			@Override
			public void onClick(ClickEvent event) {
				logger.finer("OneAcquisitionSpegrogramChart: clickHandler");
				if (currentFreq <= 0) {
					logger.finer("Freq is 0 -- doing nothing");
					return;
				}
				VerticalPanel powerVsTimeHpanel = new VerticalPanel();
				new PowerVsTime(mSpectrumBrowser, powerVsTimeHpanel, mSensorId,
						tStartTimeUtc, (long) (currentFreq * 1E6),
						canvasPixelWidth, canvasPixelHeight);
				new PowerSpectrum(mSpectrumBrowser, powerVsTimeHpanel,
						mSensorId, tStartTimeUtc, currentTime, mSubBandMinFreq,
						mSubBandMaxFreq, canvasPixelWidth, canvasPixelHeight);
				tabPanel.add(powerVsTimeHpanel, NumberFormat.getFormat("00.00")
						.format(currentTime) + " Hours");
			}
		});

		spectrogramCanvas.getContext2d().drawImage(imageElement, 0, 0);
		spectrogramCanvas.getContext2d().rect(0, 0, canvasPixelWidth,
				canvasPixelHeight);
		spectrogramPanel
				.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
		spectrogramPanel.clear();
		spectrogramPanel.setHeight(canvasPixelHeight + "px");
		spectrogramPanel.add(spectrogramCanvas);
		spectrogramPanel.add(xaxisPanel);

		freqPanel.setHeight(canvasPixelHeight + "px");
		logger.log(Level.FINER, "Image Height " + canvasPixelHeight);

		yPixelsPerMegahertz = (double) (canvasPixelHeight)
				/ (double) (maxFreqMhz - minFreqMhz);
		logger.finer("yPixelsPerMegaherz = " + yPixelsPerMegahertz
				+ "canvasPixelHeight " + canvasPixelHeight);

		if (cmapUrl != null) {
			ImagePreloader.load(cmapUrl, new ImageLoadHandler() {

				@Override
				public void imageLoaded(ImageLoadEvent event) {
					FitImage image = new FitImage();
					// TODO -- make this width part of CSS
					image.setFixedWidth(30);
					image.setHeight(canvasPixelHeight + "px");
					image.setUrl(event.getImageUrl());
					image.setPixelSize(30, canvasPixelHeight);
					ImageElement imageElement = ImageElement.as(image
							.getElement());
					imageElement.setAttribute("HEIGHT", canvasPixelHeight
							+ "px");

					image.setVisible(true);
					if (powerMapImage != null) {
						powerMapPanel.remove(powerMapImage);

					}
					powerMapPanel.add(image);
					powerMapImage = image;
					powerMapPanel.setHeight(canvasPixelHeight + "px");

				}
			});
		}

	}

	private void setSpectrogramImage() {
		try {

			spectrogramImage = new FitImage();
			// spectrogramImage.setWidth(canvasPixelWidth + "px");
			spectrogramImage.setPixelSize(canvasPixelWidth, canvasPixelHeight);
			// spectrogramImage.setFixedWidth(canvasPixelWidth);
			spectrogramImage.addLoadHandler(new LoadHandler() {

				@Override
				public void onLoad(LoadEvent event) {

					logger.fine("Image loaded");
					handleSpectrogramLoadEvent();

				}
			});
			spectrogramImage.setVisible(false);

			ImageElement imageElement = ImageElement.as(spectrogramImage
					.getElement());
			imageElement.setAttribute("HEIGHT", canvasPixelHeight + "px");
			spectrogramImage.setHeight(canvasPixelHeight + "px");

			logger.log(Level.FINER, "Setting URL " + spectrogramUrl);
			spectrogramImage.addErrorHandler(new ErrorHandler() {

				@Override
				public void onError(ErrorEvent event) {
					logger.log(Level.SEVERE, "Error loading image");
					Window.alert("Error loading image");

				}
			});

			spectrogramImage.setUrl(spectrogramUrl);
			RootPanel.get().add(spectrogramImage);

		} catch (Exception ex) {
			logger.log(Level.SEVERE, "Error retrieving image", ex);
		}
	}

	private float round(double value) {
		return (float)( (int) (value * 100) / 100.0);
	}

	private void drawOccupancyChart() {
		final DataTable dataTable = DataTable.create();
		dataTable.addColumn(ColumnType.NUMBER, " Hours since start of day.");
		dataTable.addColumn(ColumnType.NUMBER, " Occupancy %");
		dataTable.addRows(timeArray.size());
		for (int i = 0; i < timeArray.size(); i++) {
			dataTable.setValue(i, 0, round(timeArray.get(i)));
			dataTable.setValue(i, 1, occupancyArray.get(i) * 100);
		}

		ChartLoader chartLoader = new ChartLoader(ChartPackage.CORECHART);

		chartLoader.loadApi(new Runnable() {

			@Override
			public void run() {
				occupancyChart = new ScatterChart();
				occupancyChart.setWidth(canvasPixelWidth + "px");
				occupancyChart.setHeight(canvasPixelHeight + "px");
				occupancyChart
						.setPixelSize(canvasPixelWidth, canvasPixelHeight);
				ScatterChartOptions options = ScatterChartOptions.create();
				options.setBackgroundColor("#f0f0f0");
				options.setPointSize(2);
				options.setWidth(canvasPixelWidth);
				options.setHeight(canvasPixelHeight);
				options.setHAxis(HAxis.create("Hours Since Start of day"));
				options.setVAxis(VAxis.create("Occupancy %"));
				occupancyChart.setStyleName("lineChart");
				occupancyChart.draw(dataTable, options);
				occupancyChart.setVisible(true);
				occupancyPanel.add(occupancyChart);
				occupancyChart.addSelectHandler(new SelectHandler() {

					@Override
					public void onSelect(SelectEvent event) {
						JsArray<Selection> selection = occupancyChart
								.getSelection();
						int row = selection.get(0).getRow();
						currentTime = timeArray.get(row);
						logger.finer("OneAcquisitionSpegrogramChart: clickHandler");
						VerticalPanel spectrumHpanel = new VerticalPanel();
						new PowerSpectrum(mSpectrumBrowser, spectrumHpanel,
								mSensorId, tStartTimeUtc, currentTime,
								mSubBandMinFreq, mSubBandMaxFreq,
								canvasPixelWidth, canvasPixelHeight);
						tabPanel.add(
								spectrumHpanel,
								NumberFormat.getFormat("00.00").format(
										currentTime)
										+ " Hours");

					}
				});

			}
		});

	}

	public String getLabel() {
		return LABEL;
	}
	
	public String getEndLabel() {
		return END_LABEL;
	}
	
	public void draw() {
		try {
			vpanel.clear();

			drawNavigation();
			HTML pageTitle = new HTML("<h2>" + END_LABEL + "</h2>");
			vpanel.add(pageTitle);
			HTML title = new HTML("<H3>Detected System = " + mSys2detect + "; Start Time = " + localDateOfAcquisition
					+ "; Occupancy Threshold = " + cutoff
					+ " dBm; Noise Floor = " + noiseFloor + "dBm.</H3>");
			
			vpanel.add(title);
			HTML help = new HTML("<p>Click on spectrogram or occupancy plot for detail. "
					+ "Arrow buttons to go to next/prev acquisition.<br/> "
					+ "Move slider and and click on redraw button to change threshold and redraw.</p>");
			vpanel.add(help);

			grid = new Grid(1, 3);

			vpanel.add(grid);
			grid.setStyleName("selectionGrid");

			VerticalPanel tab1Panel = new VerticalPanel();

			hpanel = new HorizontalPanel();

			hpanel.setSpacing(10);
			hpanel.setStyleName("spectrogram");
			xaxisPanel = new HorizontalPanel();
			xaxisPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
			HorizontalPanel xaxis = new HorizontalPanel();
			xaxis.setWidth(canvasPixelWidth + 30 + "px");
			xaxis.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
			xaxis.add(new Label("0"));
			xaxis.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			xaxis.add(new Label("Time (hours) since start of day"));
			xaxis.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_RIGHT);
			xaxis.add(new Label(Double.toString(timeDelta)));
			xaxisPanel.add(xaxis);

			// Attach the previous reading button.

			if (prevAcquisitionTime != tStartTimeUtc) {

				final Button prevDayButton = new Button();
				prevDayButton.setEnabled(true);
				prevDayButton.addClickHandler(new ClickHandler() {

					@Override
					public void onClick(ClickEvent event) {
						mSelectionTime = prevAcquisitionTime;
						prevDayButton.setEnabled(false);
						vpanel.clear();
						vpanel.add(pleaseWaitImage);
						mSpectrumBrowser
								.getSpectrumBrowserService()
								.generateSingleDaySpectrogramAndOccupancy(
										mSpectrumBrowser.getSessionId(),
										mSensorId,
										prevAcquisitionTime,
										mSys2detect,
										mMinFreq,
										mMaxFreq,
										mSubBandMinFreq,
										mSubBandMaxFreq,
										cutoff,
										SweptFrequencyOneDaySpectrogramChart.this);

					}
				});

				prevDayButton
						.setHTML("<img border='0' src='myicons/left-arrow.png' />");

				grid.setWidget(0, 0, prevDayButton);
			}

			// Attach the labels for the spectrogram power
			VerticalPanel powerLevelPanel = new VerticalPanel();
			powerLevelPanel.setWidth(100 + "px");
			this.maxPowerLabel = new Label();
			this.minPowerLabel = new Label();
			powerLevelPanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_TOP);
			powerLevelPanel.add(maxPowerLabel);
			powerLevelPanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
			powerLevelPanel.add(new Label("Power (dBm) "));
			powerLevelPanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_BOTTOM);
			powerLevelPanel.add(minPowerLabel);
			// Attach labels for the frequency.
			freqPanel = new VerticalPanel();
			freqPanel.setWidth(100 + "px");
			powerLevelPanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_TOP);
			freqPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_TOP);
			freqPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_RIGHT);
			freqPanel.add(new Label(Double.toString(maxFreqMhz)));

			freqPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);
			freqPanel.add(new Label("Frequency (MHz)"));
			freqPanel.setVerticalAlignment(HasVerticalAlignment.ALIGN_BOTTOM);
			freqPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_RIGHT);
			freqPanel.add(new Label(Double.toString(minFreqMhz)));
			logger.finest("minFreq = " + minFreqMhz);
			powerMapPanel = new HorizontalPanel();
			powerMapPanel.setWidth(30 + "px");
			hpanel.add(freqPanel);
			spectrogramPanel = new VerticalPanel();

			HorizontalPanel spectrogramAndPowerMapPanel = new HorizontalPanel();
			spectrogramAndPowerMapPanel.add(spectrogramPanel);
			spectrogramAndPowerMapPanel.add(powerMapPanel);
			hpanel.add(spectrogramAndPowerMapPanel);
			currentValue = new Label(
					"Click on spectrogram for power spectrum at selected time.");
			tab1Panel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			tab1Panel.add(currentValue);
			tab1Panel.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
			tab1Panel.add(hpanel);
			String helpString = "Single click for power spectrum.";

			// Add the slider bar for min occupancy selection.
			occupancyMinPowerVpanel = new VerticalPanel();
			occupancyMinPowerVpanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_LEFT);
			occupancyMinPowerVpanel
					.setVerticalAlignment(HasVerticalAlignment.ALIGN_MIDDLE);

			occupancyMinPowerSliderBar = new SliderBarSimpleVertical(100,
					canvasPixelHeight + "px", true);
			occupancyMinPowerVpanel.add(occupancyMinPowerSliderBar);

			occupancyMinPowerSliderBar.setMaxValue(100);

			this.occupancyMinPowerLabel = new Label();
			occupancyMinPowerVpanel.add(occupancyMinPowerLabel);
			final Button generateSpectrogramButton = new Button(
					"Cutoff and Redraw");
			grid.setWidget(0, 1, generateSpectrogramButton);
			generateSpectrogramButton.addClickHandler(new ClickHandler() {
				@Override
				public void onClick(ClickEvent event) {
					generateSpectrogramButton.setEnabled(false);
					mSpectrumBrowser.getSpectrumBrowserService()
							.generateSingleDaySpectrogramAndOccupancy(
									mSpectrumBrowser.getSessionId(), mSensorId,
									mSelectionTime, mSys2detect, mMinFreq, mMaxFreq,
									mSubBandMinFreq, mSubBandMaxFreq,
									occupancyMinPower,
									SweptFrequencyOneDaySpectrogramChart.this);

				}
			});
			occupancyMinPowerSliderBar
					.addBarValueChangedHandler(new OccupancyMinPowerSliderHandler(
							occupancyMinPowerLabel));
			int initialValue = (int) ((double) (maxPower - cutoff)
					/ (double) (maxPower - minPower) * 100 + 0.5);
			occupancyMinPowerSliderBar.setValue(initialValue);

			hpanel.add(occupancyMinPowerVpanel);

			spectrogramPanel.setTitle(helpString);
			spectrumAndOccupancyPanel = new VerticalPanel();
			spectrumAndOccupancyPanel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			tab1Panel
					.setHorizontalAlignment(HasHorizontalAlignment.ALIGN_CENTER);
			tab1Panel.add(spectrumAndOccupancyPanel);

			occupancyPanel = new VerticalPanel();
			occupancyPanel.setWidth(canvasPixelWidth + "px");
			occupancyPanel.setHeight(canvasPixelHeight + "px");
			occupancyPanel.setPixelSize(canvasPixelWidth, canvasPixelHeight);

			// Attach the next spectrogram panel.
			if (nextAcquisitionTime != tStartTimeUtc) {
				final Button nextDayButton = new Button();
				nextDayButton.setEnabled(true);
				nextDayButton.addClickHandler(new ClickHandler() {

					@Override
					public void onClick(ClickEvent event) {
						logger.finer("getting next spectrogram");
						try {
							mSelectionTime = nextAcquisitionTime;
							nextDayButton.setEnabled(false);
							mSpectrumBrowser
									.getSpectrumBrowserService()
									.generateSingleDaySpectrogramAndOccupancy(
											mSpectrumBrowser.getSessionId(),
											mSensorId,
											nextAcquisitionTime,
											mSys2detect,
											mMinFreq,
											mMaxFreq,
											mSubBandMinFreq,
											mSubBandMaxFreq,
											cutoff,
											SweptFrequencyOneDaySpectrogramChart.this);
						} catch (Throwable th) {
							logger.log(Level.SEVERE,
									"Error calling spectrum browser service",
									th);
						}

					}
				});
				nextDayButton
						.setHTML("<img border='0' src='myicons/right-arrow.png' />");
				grid.setWidget(0, 2, nextDayButton);

			}
			setSpectrogramImage();
			drawOccupancyChart();
			tabPanel = new TabPanel();
			tabPanel.add(tab1Panel, "[Spectrogram]");
			tabPanel.add(occupancyPanel, "[Occupancy]");
			tabPanel.selectTab(0);
			vpanel.add(tabPanel);

		} catch (Throwable ex) {
			logger.log(Level.SEVERE, "Problem drawing specgtrogram", ex);
		}
	}

	@Override
	public void onFailure(Throwable throwable) {
		logger.log(Level.SEVERE, "Error communicating with server", throwable);
		mSpectrumBrowser.displayError("Error communicating with server");
	}

}
