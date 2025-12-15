/**
 * SCO Integration Example
 * Complete working example of SCO/ECO integration with Abraxas
 */

import { analyzeSCO, scoToWeatherSignals } from "../server/abraxas/pipelines/sco-analyzer";
import { computeSCOCompression, scoToWeatherNarrative } from "../server/abraxas/weather_engine/modules/sco-compression";
import type { SCOLexiconEntry } from "../server/abraxas/integrations/sco-bridge";

// ================================
// Example 1: Basic Analysis
// ================================

async function example1_basicAnalysis() {
  console.log("\n=== Example 1: Basic SCO Analysis ===\n");

  const texts = [
    "I love listening to Aphex Twins on repeat.",
    "Apex Twin's music is absolutely legendary.",
    "Have you heard the new Aphex Twins album?",
    "Apex Twin is a genius producer.",
  ];

  const result = await analyzeSCO({
    texts,
    domain: "music",
  });

  console.log(`Detected ${result.events.length} compression events`);
  console.log(`Compression Pressure: ${result.signals.compressionPressure}`);
  console.log(`Drift Intensity: ${result.signals.driftIntensity}`);
  console.log(`\nEvents:`);

  for (const event of result.events) {
    console.log(`  - "${event.original_token}" → "${event.replacement_token}"`);
    console.log(`    Tier: ${event.tier}, Status: ${event.status}`);
    console.log(`    Phonetic Similarity: ${event.phonetic_similarity}`);
    console.log(`    Compression Pressure: ${event.compression_pressure}`);
  }

  return result;
}

// ================================
// Example 2: Weather Integration
// ================================

async function example2_weatherIntegration() {
  console.log("\n=== Example 2: Weather Engine Integration ===\n");

  const texts = [
    "We arrived in the nit of time.",
    "It was in the nick of time that we made it.",
    "Just in the nit of time!",
    "Nick of time arrival saved us.",
  ];

  // Run SCO analysis
  const result = await analyzeSCO({
    texts,
    domain: "idiom",
  });

  // Generate weather signal
  const weatherSignal = computeSCOCompression(result.events);

  console.log("Weather Signal:");
  console.log(`  Intensity: ${(weatherSignal.intensity * 100).toFixed(1)}%`);
  console.log(`  Pressure: ${weatherSignal.pressure}`);
  console.log(`  Dominant Axis: ${weatherSignal.dominantAxis}`);
  console.log(`  Event Count: ${weatherSignal.eventCount}`);
  console.log(`\nForecast:\n${weatherSignal.forecast}`);

  // Generate narrative
  const narrative = scoToWeatherNarrative(weatherSignal);
  console.log(`\nWeather Narrative:\n${narrative}`);

  // Convert to weather engine signals
  const signals = scoToWeatherSignals(result);
  console.log(`\nGenerated ${signals.length} weather signals`);

  return { result, weatherSignal, signals };
}

// ================================
// Example 3: Custom Lexicon
// ================================

async function example3_customLexicon() {
  console.log("\n=== Example 3: Custom Lexicon ===\n");

  const customLexicon: SCOLexiconEntry[] = [
    {
      canonical: "ethereum",
      variants: ["etherium", "etherum", "etheruem"],
    },
    {
      canonical: "bitcoin",
      variants: ["bitcon", "bit coin", "bitcoins"],
    },
    {
      canonical: "blockchain",
      variants: ["block chain", "blockchains"],
    },
  ];

  const texts = [
    "I invested in etherium last year.",
    "Bitcon prices are soaring.",
    "The block chain technology is revolutionary.",
    "Ethereum is a solid investment.",
    "Bitcoin reached new highs.",
  ];

  const result = await analyzeSCO({
    texts,
    domain: "crypto",
    customLexicon,
  });

  console.log(`Found ${result.events.length} brand compression events`);

  for (const event of result.events) {
    console.log(`\n"${event.original_token}" → "${event.replacement_token}"`);
    console.log(`  Transparency Delta: ${event.semantic_transparency_delta}`);
    console.log(`  Intent Preservation: ${event.intent_preservation_score}`);
    console.log(`  Observed Frequency: ${event.observed_frequency}`);
  }

  return result;
}

// ================================
// Example 4: RDV Analysis
// ================================

async function example4_rdvAnalysis() {
  console.log("\n=== Example 4: RDV (Replacement Direction Vector) Analysis ===\n");

  const texts = [
    "lol this meme is unhinged and silly af",
    "literally based take, no irony detected",
    "this is pointless and doomed to fail",
    "the official policy says we must comply",
  ];

  const result = await analyzeSCO({
    texts,
    domain: "general",
  });

  const weatherSignal = computeSCOCompression(result.events);

  console.log("Affective Axes:");
  for (const [axis, value] of Object.entries(weatherSignal.affect)) {
    if (value > 0.01) {
      console.log(`  ${axis}: ${value.toFixed(4)}`);
    }
  }

  console.log(`\nDominant Axis: ${weatherSignal.dominantAxis}`);

  return weatherSignal;
}

// ================================
// Example 5: Batch Processing
// ================================

async function example5_batchProcessing() {
  console.log("\n=== Example 5: Batch Multi-Domain Processing ===\n");

  const musicCorpus = [
    "Aphex Twins is my favorite artist.",
    "I saw Apex Twin live once.",
  ];

  const idiomCorpus = [
    "We got there in the nit of time.",
    "For all intensive purposes, it worked.",
  ];

  const cryptoCorpus = [
    "I bought some etherium tokens.",
    "Bitcon mining is expensive.",
  ];

  const corpora = [
    { domain: "music", texts: musicCorpus },
    { domain: "idiom", texts: idiomCorpus },
    { domain: "crypto", texts: cryptoCorpus },
  ];

  // Note: batchAnalyzeSCO would need to be imported from sco-analyzer
  // This is a manual version for the example
  const results = await Promise.all(
    corpora.map(({ domain, texts }) => analyzeSCO({ texts, domain }))
  );

  console.log("Batch Results:");
  for (let i = 0; i < results.length; i++) {
    const { domain } = corpora[i];
    const result = results[i];
    console.log(`  ${domain}: ${result.events.length} events, pressure=${result.signals.compressionPressure.toFixed(2)}`);
  }

  return results;
}

// ================================
// Run All Examples
// ================================

async function runAllExamples() {
  try {
    await example1_basicAnalysis();
    await example2_weatherIntegration();
    await example3_customLexicon();
    await example4_rdvAnalysis();
    await example5_batchProcessing();

    console.log("\n=== All Examples Complete ===\n");
  } catch (error) {
    console.error("Example error:", error);
    process.exit(1);
  }
}

// Run if called directly
if (require.main === module) {
  runAllExamples();
}

export {
  example1_basicAnalysis,
  example2_weatherIntegration,
  example3_customLexicon,
  example4_rdvAnalysis,
  example5_batchProcessing,
};
