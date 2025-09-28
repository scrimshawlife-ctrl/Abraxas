import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Eye, TrendingUp, Zap, Shield } from "lucide-react";

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-gray-900 to-black">
      {/* Dark wash over background */}
      <div className="absolute inset-0 bg-black/50"></div>
      
      <div className="relative z-10 container mx-auto px-4 py-16">
        <div className="text-center space-y-8">
          {/* Hero Section */}
          <div className="space-y-6">
            <div className="flex items-center justify-center gap-2 mb-4">
              <Eye className="h-8 w-8 text-purple-400" />
              <h1 className="text-4xl md:text-6xl font-bold text-white">
                ABRAXAS
              </h1>
            </div>
            
            <p className="text-xl md:text-2xl text-gray-300 max-w-3xl mx-auto">
              Mystical Trading Oracle • Sources & methods sealed • Not financial advice
            </p>
            
            <p className="text-lg text-gray-400 max-w-2xl mx-auto">
              Combine ancient wisdom with modern market analysis through our mystical trading algorithms and dynamic watchlist system.
            </p>
          </div>

          {/* Features Grid */}
          <div className="grid md:grid-cols-3 gap-6 max-w-4xl mx-auto mt-16">
            <Card className="bg-gray-800/50 border-purple-500/30">
              <CardHeader>
                <TrendingUp className="h-8 w-8 text-purple-400 mx-auto" />
                <CardTitle className="text-white">Dynamic Watchlists</CardTitle>
                <CardDescription className="text-gray-300">
                  AI-powered market analysis for growth opportunities and short candidates
                </CardDescription>
              </CardHeader>
            </Card>
            
            <Card className="bg-gray-800/50 border-purple-500/30">
              <CardHeader>
                <Zap className="h-8 w-8 text-amber-400 mx-auto" />
                <CardTitle className="text-white">Mystical Indicators</CardTitle>
                <CardDescription className="text-gray-300">
                  Proprietary algorithms that blend traditional analysis with esoteric insights
                </CardDescription>
              </CardHeader>
            </Card>
            
            <Card className="bg-gray-800/50 border-purple-500/30">
              <CardHeader>
                <Shield className="h-8 w-8 text-green-400 mx-auto" />
                <CardTitle className="text-white">Secure Analysis</CardTitle>
                <CardDescription className="text-gray-300">
                  Personal watchlists and trading insights protected by modern authentication
                </CardDescription>
              </CardHeader>
            </Card>
          </div>

          {/* Call to Action */}
          <div className="mt-16 space-y-6">
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Button 
                size="lg" 
                variant="default"
                className="bg-purple-600 hover:bg-purple-700 text-white"
                onClick={() => window.location.href = '/api/login'}
                data-testid="button-login"
              >
                Enter the Oracle
              </Button>
              
              <Badge variant="outline" className="text-purple-400 border-purple-400">
                Mystical • Analytical • Secure
              </Badge>
            </div>
            
            <p className="text-sm text-gray-500 max-w-md mx-auto">
              By entering, you acknowledge this is not financial advice. 
              Past mystical insights do not guarantee future results.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}