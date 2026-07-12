// services/ml/mockML.js
const processPrescription = async (imageUrl) => {
    await new Promise(resolve => setTimeout(resolve, 3000))

    const mockMedicines = [
        {
            name: "Panadol",
            genericName: "Paracetamol",
            dosage: "500mg",
            frequency: "Twice daily",
            duration: "5 days",
            instructions: "After meal",
            confidence: 0.91,
            needsReview: false
        },
        {
            name: "Amoxicillin",
            genericName: "Amoxicillin",
            dosage: "250mg",
            frequency: "Three times daily",
            duration: "7 days",
            instructions: "Before meal",
            confidence: 0.65,
            needsReview: true
        }
    ]

    const avgConfidence = mockMedicines.reduce((sum, m) => sum + m.confidence, 0) / mockMedicines.length
    return {
        medicines: mockMedicines,
        rawText: "Panadol 500mg BD x 5d, Amoxicillin 250mg TDS x 7d",
        confidenceScore: avgConfidence
    }
}

export { processPrescription }